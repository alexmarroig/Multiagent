"""Top-level orchestration for the Agent Operating System."""

from __future__ import annotations

from collections import defaultdict
import time
from dataclasses import dataclass
from typing import Any

from core.task_queue import DistributedTaskQueue

from communication.agent_mailbox import AgentMailbox
from communication.event_bus import EventBus
from core.autonomy_engine import AutonomyEngine
from core.load_manager import LoadManager
from core.scheduler import SchedulingKernel
from governance.guardrails import Guardrails
from governance.human_approval_service import HumanApprovalService
from governance.policy_engine import PolicyEngine
from monitoring.telemetry_service import TelemetryService
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
        task_queue: DistributedTaskQueue | None = None,
        max_schedule_tasks: int = 500,
        max_active_runs_per_tenant: int = 128,
        max_spawn_requests_per_run: int = 100,
        run_timeout_seconds: float = 120.0,
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
        self.task_queue = task_queue
        self.max_schedule_tasks = max(1, max_schedule_tasks)
        self.max_active_runs_per_tenant = max(1, max_active_runs_per_tenant)
        self.max_spawn_requests_per_run = max(1, max_spawn_requests_per_run)
        self.run_timeout_seconds = max(1.0, run_timeout_seconds)
        self._active_runs_by_tenant: dict[str, int] = defaultdict(int)

    def run(self, context: OrchestrationContext, objective: dict[str, Any]) -> dict[str, Any]:
        if self._active_runs_by_tenant[context.tenant_id] >= self.max_active_runs_per_tenant:
            self.telemetry.record("orchestration.tenant_concurrency_rejected", {"request_id": context.request_id, "tenant_id": context.tenant_id})
            return {"status": "deferred", "reason": "tenant_concurrency_limit"}

        self._active_runs_by_tenant[context.tenant_id] += 1
        try:
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
            if self.task_queue is not None and not self.task_queue.can_schedule_new_tasks():
                self.telemetry.record("orchestration.backpressure_rejected", {"request_id": context.request_id})
                return {"status": "deferred", "reason": "queue_backpressure"}

            if objective.get("run_through_runtime_pipeline") is False:
                self.telemetry.record("orchestration.policy_rejected", {"request_id": context.request_id, "reason": "runtime_pipeline_required"})
                return {"status": "rejected", "reason": "runtime_pipeline_required"}

            spawn_requests = int(objective.get("spawn_count", 0) or 0)
            if spawn_requests > self.max_spawn_requests_per_run:
                self.telemetry.record("orchestration.spawn_capped", {"request_id": context.request_id, "spawn_requested": spawn_requests, "spawn_cap": self.max_spawn_requests_per_run})
                objective = {**objective, "spawn_count": self.max_spawn_requests_per_run}

            start = time.monotonic()
            schedule = self.scheduler.generate_plan(graph_id, objective)
            if isinstance(schedule, list) and len(schedule) > self.max_schedule_tasks:
                schedule = schedule[: self.max_schedule_tasks]
                self.telemetry.record("orchestration.schedule_truncated", {"request_id": context.request_id, "max_schedule_tasks": self.max_schedule_tasks})
            if (time.monotonic() - start) > self.run_timeout_seconds:
                self.telemetry.record("orchestration.timed_out", {"request_id": context.request_id, "stage": "planning"})
                return {"status": "failed", "reason": "planning_timeout", "graph_id": graph_id}

            run_report = self.autonomy_engine.execute(graph_id=graph_id, schedule=schedule)
            if (time.monotonic() - start) > self.run_timeout_seconds:
                self.telemetry.record("orchestration.timed_out", {"request_id": context.request_id, "stage": "execution"})
                return {"status": "failed", "reason": "execution_timeout", "graph_id": graph_id}

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
        except Exception as exc:  # noqa: BLE001
            self.telemetry.record("orchestration.failed", {"request_id": context.request_id, "error": str(exc)})
            return {"status": "failed", "graph_id": context.request_id, "reason": str(exc)}
        finally:
            self._active_runs_by_tenant[context.tenant_id] = max(0, self._active_runs_by_tenant[context.tenant_id] - 1)
