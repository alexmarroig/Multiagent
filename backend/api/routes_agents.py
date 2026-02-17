"""Rotas de execução de agentes."""

from __future__ import annotations

import asyncio
import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends

from auth.dependencies import get_current_user
from db.supabase_client import get_supabase
from models.schemas import FlowConfig
from orchestrator.crew_builder import build_crew_from_config
from orchestrator.event_stream import make_event, publish_event

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def execute_flow(flow: FlowConfig) -> None:
    """Executa fluxo e envia eventos da sessão."""
    supabase = get_supabase()
    started = datetime.utcnow()
    event_log: list[dict[str, Any]] = []

    start_event = make_event(
        flow.session_id,
        "system",
        "AgentOS",
        "thinking",
        "Iniciando execução do fluxo",
    )
    event_log.append(start_event.model_dump(mode="json"))
    await publish_event(flow.session_id, start_event)

    try:
        # Eventos por nó para suportar status visual no canvas.
        for node in flow.nodes:
            ev = make_event(
                flow.session_id,
                node.id,
                node.label,
                "thinking",
                f"{node.label} iniciando etapa.",
            )
            event_log.append(ev.model_dump(mode="json"))
            await publish_event(flow.session_id, ev)

        crew = build_crew_from_config(flow)
        result = await asyncio.to_thread(crew.kickoff, inputs=flow.inputs)

        for node in flow.nodes:
            ev = make_event(
                flow.session_id,
                node.id,
                node.label,
                "result",
                f"{node.label} concluiu sua etapa.",
            )
            event_log.append(ev.model_dump(mode="json"))
            await publish_event(flow.session_id, ev)

        result_event = make_event(
            flow.session_id,
            "supervisor",
            "SupervisorAgent",
            "result",
            str(result),
        )
        done_event = make_event(
            flow.session_id,
            "system",
            "AgentOS",
            "done",
            "Execução finalizada",
        )
        event_log.extend(
            [result_event.model_dump(mode="json"), done_event.model_dump(mode="json")]
        )
        await publish_event(flow.session_id, result_event)
        await publish_event(flow.session_id, done_event)

        duration = int((datetime.utcnow() - started).total_seconds())
        (
            supabase.table("executions")
            .update(
                {
                    "status": "done",
                    "result": {"output": str(result)},
                    "events": event_log,
                    "completed_at": datetime.utcnow().isoformat(),
                    "duration_seconds": duration,
                }
            )
            .eq("session_id", flow.session_id)
            .execute()
        )
    except Exception as exc:
        error_payload = {"error": str(exc), "trace": traceback.format_exc()}
        error_event = make_event(flow.session_id, "system", "AgentOS", "error", error_payload)
        event_log.append(error_event.model_dump(mode="json"))
        await publish_event(flow.session_id, error_event)
        (
            supabase.table("executions")
            .update(
                {
                    "status": "error",
                    "result": error_payload,
                    "events": event_log,
                    "completed_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("session_id", flow.session_id)
            .execute()
        )


@router.post("/run")
async def run_flow(
    flow: FlowConfig,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> dict:
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
            }
        )
        .execute()
    )

    background_tasks.add_task(execute_flow, flow)
    return {"session_id": session_id, "status": "running"}


@router.get("/templates")
async def list_templates() -> list[dict]:
    # Catálogo alinhado aos agentes suportados no enum AgentType.
    return [
        {
            "id": "travel_agency",
            "name": "Agência de Turismo",
            "description": "travel → financial → meeting",
            "agents": ["travel", "financial", "meeting"],
            "color": "orange",
            "inputs": ["destination", "checkin", "checkout", "budget_brl", "adults"],
        },
        {
            "id": "marketing_company",
            "name": "Empresa de Marketing",
            "description": "marketing → excel → phone → supervisor",
            "agents": ["marketing", "excel", "phone", "supervisor"],
            "color": "blue",
            "inputs": ["product", "audience"],
        },
        {
            "id": "financial_office",
            "name": "Escritório Financeiro",
            "description": "financial → excel → supervisor",
            "agents": ["financial", "excel", "supervisor"],
            "color": "green",
            "inputs": ["tickers", "period"],
        },
        {
            "id": "executive_assistant",
            "name": "Assistente Executivo",
            "description": "meeting → phone → supervisor",
            "agents": ["meeting", "phone", "supervisor"],
            "color": "purple",
            "inputs": ["date", "attendees", "phone_number"],
        },
    ]
