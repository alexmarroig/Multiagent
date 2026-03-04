"""Top-level orchestration for the Agent Operating System."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentos.communication.agent_mailbox import AgentMailbox
from agentos.communication.event_bus import EventBus
from agentos.core.autonomy_engine import AutonomyEngine
from agentos.core.load_manager import LoadManager
from agentos.core.scheduler import SchedulingKernel
from agentos.governance.guardrails import Guardrails
from agentos.governance.human_approval_service import HumanApprovalService
from agentos.governance.policy_engine import PolicyEngine
from agentos.monitoring.telemetry_service import TelemetryService
from tasks.task_graph_engine import TaskGraphEngine


@dataclass(slots=True)
class OrchestrationContext:
    tenant_id: str
    request_id: str
    initiator: str
    budget_limit_usd: float
    metadata: dict[str, Any]


class Orchestrator:
    """Coordinates planning, execution, governance, and observability."""

    def __init__(
        self,
        *,
        task_graph: TaskGraphEngine,
        autonomy_engine: AutonomyEngine,
        scheduler: SchedulingKernel,
        load_manager: LoadManager,
        policy_engine: PolicyEngine,
        approval_service: HumanApprovalService,
        guardrails: Guardrails,
        telemetry: TelemetryService,
        event_bus: EventBus,
        mailbox: AgentMailbox,
    ) -> None:
        self.task_graph = task_graph
        self.autonomy_engine = autonomy_engine
        self.scheduler = scheduler
        self.load_manager = load_manager
        self.policy_engine = policy_engine
        self.approval_service = approval_service
        self.guardrails = guardrails
        self.telemetry = telemetry
        self.event_bus = event_bus
        self.mailbox = mailbox

    def run(self, context: OrchestrationContext, objective: dict[str, Any]) -> dict[str, Any]:
        self.telemetry.record("orchestration.started", {"request_id": context.request_id, "objective": objective})
        policy_decision = self.policy_engine.evaluate(objective, actor=context.initiator)
        if not policy_decision.allowed:
            return {"status": "rejected", "reason": policy_decision.reason}

        if policy_decision.requires_human_approval:
            approved = self.approval_service.request_approval(context.request_id, objective, policy_decision.reason)
            if not approved:
                return {"status": "rejected", "reason": "human_approval_denied"}

        graph_id = context.request_id
        if hasattr(self.task_graph, "create_graph"):
            graph_id = self.task_graph.create_graph(context.request_id, objective)
        elif hasattr(self.task_graph, "ingest_plan"):
            self.task_graph.ingest_plan(objective.get("tasks", []))
        schedule = self.scheduler.generate_plan(graph_id, objective)
        run_report = self.autonomy_engine.execute(graph_id=graph_id, schedule=schedule)
        guarded_report = self.guardrails.enforce(run_report, budget_limit_usd=context.budget_limit_usd)
        placement = self.load_manager.snapshot()

        result = {
            "status": "completed",
            "graph_id": graph_id,
            "run_report": guarded_report,
            "worker_state": placement,
        }
        self.telemetry.record("orchestration.completed", result)
        return result
