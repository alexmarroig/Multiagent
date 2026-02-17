"""Rotas de execução de agentes."""

from __future__ import annotations

import asyncio
import traceback
import uuid

from fastapi import APIRouter, BackgroundTasks

from models.schemas import FlowConfig
from orchestrator.event_stream import make_event, publish_event

router = APIRouter(prefix="/api/agents", tags=["agents"])


async def execute_flow(flow: FlowConfig) -> None:
    """Executa fluxo e envia eventos da sessão."""
    await publish_event(
        flow.session_id,
        make_event(flow.session_id, "system", "AgentOS", "thinking", "Iniciando execução do fluxo"),
    )
    try:
        from orchestrator.crew_builder import build_crew_from_config

        crew = build_crew_from_config(flow)
        result = await asyncio.to_thread(crew.kickoff, inputs=flow.inputs)
        await publish_event(
            flow.session_id,
            make_event(flow.session_id, "supervisor", "SupervisorAgent", "result", str(result)),
        )
        await publish_event(
            flow.session_id,
            make_event(flow.session_id, "system", "AgentOS", "done", "Execução finalizada"),
        )
    except Exception as exc:
        await publish_event(
            flow.session_id,
            make_event(
                flow.session_id,
                "system",
                "AgentOS",
                "error",
                {"error": str(exc), "trace": traceback.format_exc()},
            ),
        )


@router.post("/run")
async def run_flow(flow: FlowConfig, background_tasks: BackgroundTasks) -> dict:
    session_id = flow.session_id or str(uuid.uuid4())
    flow = flow.model_copy(update={"session_id": session_id})
    background_tasks.add_task(execute_flow, flow)
    return {"session_id": session_id, "status": "running"}


@router.get("/templates")
async def list_templates() -> list[dict]:
    return [
        {
            "id": "travel_agency",
            "name": "Agência de Turismo",
            "description": "Pesquisa, reserva e consolidação de custos.",
            "agents": ["travel", "financial", "meeting", "supervisor"],
            "color": "orange",
            "inputs": ["destination", "budget_brl", "days"],
        },
        {
            "id": "marketing_company",
            "name": "Empresa de Marketing",
            "description": "Pesquisa de mercado e execução de campanhas.",
            "agents": ["marketing", "financial", "excel", "supervisor"],
            "color": "blue",
            "inputs": ["segment", "product", "goal"],
        },
        {
            "id": "financial_office",
            "name": "Escritório Financeiro",
            "description": "Análise financeira e geração de relatório executivo.",
            "agents": ["financial", "excel", "meeting", "supervisor"],
            "color": "green",
            "inputs": ["ticker", "period"],
        },
        {
            "id": "executive_assistant",
            "name": "Assistente Executivo",
            "description": "Organização de agenda com comunicações automáticas.",
            "agents": ["meeting", "phone", "travel", "supervisor"],
            "color": "purple",
            "inputs": ["attendees", "meeting_topic", "timeslots"],
        },
    ]
