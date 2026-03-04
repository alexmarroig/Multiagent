"""Rotas de execução de agentes."""

from __future__ import annotations

import asyncio
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from agentos.backend.auth.dependencies import get_current_user
from agentos.backend.autonomy.agent_loop import AutonomousAgentLoop, LoopGuardrails
from agentos.backend.autonomy.task_decomposer import DecompositionConstraints, TaskDecomposer
from agentos.backend.db.supabase_client import get_supabase
from agentos.backend.models.schemas import FlowConfig
from agentos.backend.observability.logging import log_structured
from agentos.backend.observability.metrics import metrics_store
from agentos.backend.orchestrator.crew_builder import ExecutionCancelledError, build_crew_from_config
from agentos.backend.orchestrator.event_stream import make_event, publish_event
from agentos.backend.orchestrator.task_queue import QueuedTask
from agentos.backend.scheduler.agent_scheduler import AgentScheduler
from agentos.backend.security.rbac import Permission, RBACAuthorizationError, RBACResource, rbac_middleware

router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = logging.getLogger("agentos-backend")
agent_scheduler = AgentScheduler()



def _authorize_agent_creation(user: dict[str, Any], tenant_id: str | None) -> None:
    context = rbac_middleware.context_from_user(user, fallback_roles=("operator",))
    resource_tenant = tenant_id or user.get("tenant_id") or user.get("organization_id")
    try:
        rbac_middleware.authorize(
            context=context,
            permission=Permission.AGENT_CREATE,
            resource=RBACResource(
                resource_type="agent",
                action="create",
                tenant_id=resource_tenant,
                scope="tenant",
            ),
        )
    except RBACAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

TERMINAL_STATUSES = {"done", "error", "cancelled"}
RUNNING_EXECUTIONS: dict[str, asyncio.Task[Any]] = {}
CANCEL_FLAGS: dict[str, asyncio.Event] = {}


def _current_status(supabase: Any, session_id: str) -> str | None:
    response = (
        supabase.table("executions")
        .select("status")
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return rows[0].get("status")


def _safe_update_execution(
    supabase: Any,
    session_id: str,
    payload: dict[str, Any],
    *,
    terminal: bool = False,
) -> None:
    if terminal:
        status = _current_status(supabase, session_id)
        if status in TERMINAL_STATUSES:
            return

    (
        supabase.table("executions")
        .update(payload)
        .eq("session_id", session_id)
        .execute()
    )


async def execute_flow(flow: FlowConfig) -> None:
    supabase = get_supabase()
    started = datetime.utcnow()
    event_log: list[dict[str, Any]] = []

    metrics_store.mark_run_started(flow.session_id)

    log_structured(
        logger,
        "flow_execution_started",
        session_id=flow.session_id,
        user_id=flow.user_id,
        agent_id="system",
    )

    cancel_event = CANCEL_FLAGS.setdefault(flow.session_id, asyncio.Event())
    RUNNING_EXECUTIONS[flow.session_id] = asyncio.current_task()  # type: ignore

    async def emit(ev) -> None:
        payload = ev.model_dump(mode="json")
        event_log.append(payload)
        try:
            await publish_event(flow.session_id, ev)
        except Exception:
            pass

    def record_event(payload: dict[str, Any]) -> None:
        event_log.append(payload)

    def is_cancelled() -> bool:
        if cancel_event.is_set():
            return True
        current = _current_status(supabase, flow.session_id)
        return current in {"cancelling", "cancelled"}

    await emit(make_event(flow.session_id, "system", "AgentOS", "thinking", "Iniciando execução autônoma"))

    try:
        crew = build_crew_from_config(flow, event_recorder=record_event, cancellation_checker=is_cancelled)
        decomposer = TaskDecomposer(
            DecompositionConstraints(
                max_depth=3,
                max_subtasks_per_task=4,
                max_total_tasks=max(6, flow.autonomy.max_iterations * 3),
                max_task_tokens=220,
            )
        )

        def planner_fn(objective: str, context: list[dict[str, Any]]) -> list[QueuedTask]:
            tasks = decomposer.decompose(objective=objective, session_id=flow.session_id, context=context)
            for task in tasks:
                task.payload = {**task.payload, "flow_inputs": flow.inputs}
            return tasks

        def execute_fn(payload: dict[str, Any]) -> Any:
            return crew.kickoff(inputs={**flow.inputs, **payload.get("payload", {})})

        loop = AutonomousAgentLoop(
            session_id=flow.session_id,
            objective=flow.autonomy.objective or "Concluir execução do fluxo",
            execute_fn=execute_fn,
            planner_fn=planner_fn,
            guardrails=LoopGuardrails(
                max_iterations=flow.autonomy.max_iterations,
                max_runtime_seconds=flow.autonomy.max_runtime_seconds,
                max_cost=flow.autonomy.max_cost,
            ),
            completion_keywords=flow.autonomy.completion_keywords,
        )

        result = await asyncio.to_thread(loop.run)

        if is_cancelled():
            raise ExecutionCancelledError("Execução cancelada durante loop autônomo.")

        await emit(make_event(flow.session_id, "system", "AgentOS", "done", "Loop autônomo finalizado"))

        duration = int((datetime.utcnow() - started).total_seconds())
        status = "done" if result.get("status") == "completed" else "stopped"

        metrics_store.mark_run_finished(flow.session_id, status)

        _safe_update_execution(
            supabase,
            flow.session_id,
            {
                "status": status,
                "result": result,
                "events": event_log,
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": duration,
            },
            terminal=True,
        )

    except (asyncio.CancelledError, ExecutionCancelledError) as exc:
        payload = {"reason": str(exc) or "Execução cancelada"}

        await emit(make_event(flow.session_id, "system", "AgentOS", "cancelled", payload))

        _safe_update_execution(
            supabase,
            flow.session_id,
            {
                "status": "cancelled",
                "result": payload,
                "events": event_log,
                "completed_at": datetime.utcnow().isoformat(),
            },
            terminal=True,
        )

    except Exception as exc:
        error_payload = {"error": str(exc), "trace": traceback.format_exc()}

        metrics_store.mark_run_finished(flow.session_id, "error")
        await emit(make_event(flow.session_id, "system", "AgentOS", "error", error_payload))

        _safe_update_execution(
            supabase,
            flow.session_id,
            {
                "status": "error",
                "result": error_payload,
                "events": event_log,
                "completed_at": datetime.utcnow().isoformat(),
            },
            terminal=True,
        )

    finally:
        RUNNING_EXECUTIONS.pop(flow.session_id, None)
        CANCEL_FLAGS.pop(flow.session_id, None)


@router.post("/run")
async def run_flow(
    flow: FlowConfig,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    _authorize_agent_creation(user, flow.inputs.get("tenant_id"))
    session_id = flow.session_id or str(uuid.uuid4())
    flow = flow.model_copy(update={"session_id": session_id, "user_id": user["id"]})

    supabase = get_supabase()

    (
        supabase.table("executions")
        .insert(
            {
                "user_id": user["id"],
                "session_id": session_id,
                "status": "running",
                "config": flow.model_dump(),
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        .execute()
    )

    CANCEL_FLAGS[session_id] = asyncio.Event()
    task = asyncio.create_task(execute_flow(flow))
    RUNNING_EXECUTIONS[session_id] = task

    if flow.autonomy.schedule_every_minutes:
        agent_scheduler.queue_periodic_task(
            job_id=f"autonomy-{session_id}",
            every_minutes=flow.autonomy.schedule_every_minutes,
            job_fn=lambda: asyncio.run(execute_flow(flow.model_copy())),
        )
        agent_scheduler.start()

    return {"session_id": session_id, "status": "running", "autonomy_enabled": flow.autonomy.enabled}


@router.post("/{session_id}/cancel")
async def cancel_flow(
    session_id: str,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    supabase = get_supabase()

    execution = (
        supabase.table("executions")
        .select("status,user_id")
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )

    rows = execution.data or []

    if not rows:
        raise HTTPException(status_code=404, detail="Execução não encontrada")

    if rows[0].get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    status = rows[0].get("status")

    if status in TERMINAL_STATUSES:
        return {"session_id": session_id, "status": status, "message": "Execução já finalizada"}

    _safe_update_execution(supabase, session_id, {"status": "cancelling", "updated_at": datetime.utcnow().isoformat()})

    cancel_event = CANCEL_FLAGS.setdefault(session_id, asyncio.Event())
    cancel_event.set()

    task = RUNNING_EXECUTIONS.get(session_id)
    if task and not task.done():
        task.cancel()

    return {"session_id": session_id, "status": "cancelling"}
