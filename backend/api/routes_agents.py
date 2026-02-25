"""Rotas de execução de agentes."""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user
from db.supabase_client import get_supabase
from models.schemas import FlowConfig
from orchestrator.crew_builder import ExecutionCancelledError, build_crew_from_config
from orchestrator.event_stream import make_event, publish_event

router = APIRouter(prefix="/api/agents", tags=["agents"])
TERMINAL_STATUSES = {"done", "error", "cancelled"}
RUNNING_EXECUTIONS: dict[str, asyncio.Task[Any]] = {}
CANCEL_FLAGS: dict[str, asyncio.Event] = {}


def _current_status(supabase: Any, session_id: str) -> str | None:
    response = (
        supabase.table("executions").select("status").eq("session_id", session_id).limit(1).execute()
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

    supabase.table("executions").update(payload).eq("session_id", session_id).execute()


async def execute_flow(flow: FlowConfig) -> None:
    """Executa fluxo e envia eventos da sessão. Persiste status/result/events no Supabase."""
    supabase = get_supabase()
    started = datetime.utcnow()
    event_log: list[dict[str, Any]] = []
    cancel_event = CANCEL_FLAGS.setdefault(flow.session_id, asyncio.Event())
    RUNNING_EXECUTIONS[flow.session_id] = asyncio.current_task()  # type: ignore[assignment]

    degraded_state = {"redis": False, "supabase": False}

    async def emit(ev) -> None:
        payload = ev.model_dump(mode="json")
        event_log.append(payload)
        try:
            await publish_event(flow.session_id, ev)
            degraded_state["redis"] = False
        except Exception:
            degraded_state["redis"] = True

    def record_event(payload: dict[str, Any]) -> None:
        event_log.append(payload)

    def is_cancelled() -> bool:
        if cancel_event.is_set():
            return True
        current = _current_status(supabase, flow.session_id)
        return current in {"cancelling", "cancelled"}

    await emit(
        make_event(
            flow.session_id,
            "system",
            "AgentOS",
            "thinking",
            "Iniciando execução do fluxo",
        )
    )

    try:
        # Eventos por nó para suportar status visual no canvas.
        for node in flow.nodes:
            label = getattr(node, "label", node.id)
            await emit(
                make_event(
                    flow.session_id,
                    node.id,
                    label,
                    "thinking",
                    f"{label} iniciando etapa.",
                )
            )

        crew = build_crew_from_config(flow, event_recorder=record_event, cancellation_checker=is_cancelled)
        result = await asyncio.to_thread(crew.kickoff, inputs=flow.inputs)

        if is_cancelled():
            raise ExecutionCancelledError("Execução cancelada após kickoff.")

        for node in flow.nodes:
            label = getattr(node, "label", node.id)
            await emit(
                make_event(
                    flow.session_id,
                    node.id,
                    label,
                    "result",
                    f"{label} concluiu sua etapa.",
                )
            )

        await emit(
            make_event(
                flow.session_id,
                "supervisor",
                "SupervisorAgent",
                "result",
                str(result),
            )
        )
        await emit(
            make_event(
                flow.session_id,
                "system",
                "AgentOS",
                "done",
                "Execução finalizada",
            )
        )

        duration = int((datetime.utcnow() - started).total_seconds())
        _safe_update_execution(
            supabase,
            flow.session_id,
            {
                "status": "done",
                "result": {"output": str(result)},
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

        try:
            await emit(make_event(flow.session_id, "system", "AgentOS", "error", error_payload))
        except Exception:
            # Se publish_event falhar, ainda garantimos o log local
            event_log.append(
                make_event(flow.session_id, "system", "AgentOS", "error", error_payload).model_dump(
                    mode="json"
                )
            )

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
    session_id = flow.session_id or str(uuid.uuid4())
    flow = flow.model_copy(update={"session_id": session_id, "user_id": user["id"]})

    supabase = get_supabase()

    try:
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Falha ao criar execution: {exc}") from exc

    CANCEL_FLAGS[session_id] = asyncio.Event()
    task = asyncio.create_task(execute_flow(flow))
    RUNNING_EXECUTIONS[session_id] = task
    return {"session_id": session_id, "status": "running"}


@router.post("/{session_id}/cancel")
async def cancel_flow(session_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    _safe_update_execution(
        supabase,
        session_id,
        {"status": "cancelling", "updated_at": datetime.utcnow().isoformat()},
    )

    cancel_event = CANCEL_FLAGS.setdefault(session_id, asyncio.Event())
    cancel_event.set()

    task = RUNNING_EXECUTIONS.get(session_id)
    if task and not task.done():
        task.cancel()

    return {"session_id": session_id, "status": "cancelling"}


@router.get("/templates")
async def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": "travel_agency",
            "name": "Agência de Turismo",
            "description": "Pesquisa, reserva e consolidação de custos.",
            "pipeline": "travel → financial → meeting → supervisor",
            "agents": ["travel", "financial", "meeting", "supervisor"],
            "color": "orange",
            "inputs": ["destination", "budget_brl", "days"],
        },
        {
            "id": "marketing_company",
            "name": "Empresa de Marketing",
            "description": "Pesquisa de mercado e execução de campanhas.",
            "pipeline": "marketing → financial → excel → supervisor",
            "agents": ["marketing", "financial", "excel", "supervisor"],
            "color": "blue",
            "inputs": ["segment", "product", "goal"],
        },
        {
            "id": "financial_office",
            "name": "Escritório Financeiro",
            "description": "Análise financeira e geração de relatório executivo.",
            "pipeline": "financial → excel → meeting → supervisor",
            "agents": ["financial", "excel", "meeting", "supervisor"],
            "color": "green",
            "inputs": ["ticker", "period"],
        },
        {
            "id": "executive_assistant",
            "name": "Assistente Executivo",
            "description": "Organização de agenda com comunicações automáticas.",
            "pipeline": "meeting → phone → travel → supervisor",
            "agents": ["meeting", "phone", "travel", "supervisor"],
            "color": "purple",
            "inputs": ["attendees", "meeting_topic", "timeslots"],
        },
    ]
