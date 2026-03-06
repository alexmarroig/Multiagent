from __future__ import annotations

from dataclasses import dataclass
import sys
import types

_fake_scheduler = types.ModuleType("core.scheduler")


class SchedulingKernel:
    def generate_plan(self, graph_id: str, objective: dict):
        return [{"step": 1}]


_fake_scheduler.SchedulingKernel = SchedulingKernel
sys.modules.setdefault("core.scheduler", _fake_scheduler)

from communication.agent_mailbox import AgentMailbox
from communication.event_bus import EventBus
from core.orchestrator import OrchestrationContext, Orchestrator
from governance.guardrails import Guardrails
from governance.human_approval_service import HumanApprovalService
from governance.policy_engine import Policy, PolicyEngine
from monitoring.telemetry_service import TelemetryService


@dataclass
class _TaskGraph:
    def create_graph(self, request_id: str, objective: dict) -> str:
        return f"graph-{request_id}"


@dataclass
class _Scheduler:
    def generate_plan(self, graph_id: str, objective: dict):
        return [{"step": 1}]


@dataclass
class _Autonomy:
    def execute(self, *, graph_id: str, schedule):
        return {"graph_id": graph_id, "steps": len(schedule)}


@dataclass
class _Load:
    def snapshot(self):
        return {"workers": 1}


def _build_orchestrator() -> Orchestrator:
    return Orchestrator(
        task_graph=_TaskGraph(),
        autonomy_engine=_Autonomy(),
        scheduler=_Scheduler(),
        load_manager=_Load(),
        policy_engine=PolicyEngine(Policy()),
        approval_service=HumanApprovalService(),
        guardrails=Guardrails(),
        telemetry=TelemetryService(),
        event_bus=EventBus(),
        mailbox=AgentMailbox(),
    )


def test_orchestrator_rejects_bypass_of_runtime_pipeline() -> None:
    orchestrator = _build_orchestrator()
    context = OrchestrationContext(
        tenant_id="tenant-a",
        request_id="r-1",
        initiator="agent-a",
        budget_limit_usd=5.0,
        metadata={},
    )
    result = orchestrator.run(context, {"run_through_runtime_pipeline": False})
    assert result["status"] == "rejected"
    assert result["reason"] == "runtime_pipeline_required"


def test_orchestrator_completes_when_runtime_pipeline_required() -> None:
    orchestrator = _build_orchestrator()
    context = OrchestrationContext(
        tenant_id="tenant-a",
        request_id="r-2",
        initiator="agent-a",
        budget_limit_usd=5.0,
        metadata={},
    )
    result = orchestrator.run(context, {"run_through_runtime_pipeline": True})
    assert result["status"] == "completed"
