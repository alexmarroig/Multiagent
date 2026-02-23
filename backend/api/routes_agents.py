"""Rotas de execução de agentes."""

from __future__ import annotations

import asyncio
import traceback
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from auth.dependencies import get_current_user
from db.supabase_client import get_supabase
from models.schemas import FlowConfig
from orchestrator.crew_builder import build_crew_from_config
from orchestrator.event_stream import make_event, publish_event

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def execute_flow(flow: FlowConfig) -> None:
    """Executa fluxo e envia eventos da sessão. Persiste status/result/events no Supabase."""
    supabase = get_supabase()
    started = datetime.utcnow()
    event_log: list[dict[str, Any]] = []

    async def emit(ev) -> None:
        payload = ev.model_dump(mode="json")
        event_log.append(payload)
        await publish_event(flow.session_id, ev)

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

        crew = build_crew_from_config(flow)
        result = await asyncio.to_thread(crew.kickoff, inputs=flow.inputs)

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

        try:
            await emit(make_event(flow.session_id, "system", "AgentOS", "error", error_payload))
        except Exception:
            # Se publish_event falhar, ainda garantimos o log local
            event_log.append(
                make_event(flow.session_id, "system", "AgentOS", "error", error_payload).model_dump(
                    mode="json"
                )
            )

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

    background_tasks.add_task(execute_flow, flow)
    return {"session_id": session_id, "status": "running"}


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
