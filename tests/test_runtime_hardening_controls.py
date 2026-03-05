from __future__ import annotations

import pytest

from communication.event_bus import EventBus
from core.runtime_pipeline import AgentAction, BudgetManager, RuntimePipeline
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask
from governance.approval_queue import ApprovalQueue
from governance.policy_engine import Policy, PolicyEngine
from workers.agent_worker import AgentWorker
from tools.sandbox_runner import SandboxRunner


class _Handler:
    def execute(self, task: QueueTask) -> dict:
        return {"ok": True, "task_id": task.task_id}


def test_queue_enforces_tenant_depth_limit() -> None:
    queue = DistributedTaskQueue(
        InMemoryQueueBackend(),
        tenant_queue_limits={"tenant-a": 1},
    )
    queue.enqueue_task({"task_id": "t1", "name": "a", "metadata": {"tenant_id": "tenant-a"}})
    with pytest.raises(OverflowError):
        queue.enqueue_task({"task_id": "t2", "name": "a", "metadata": {"tenant_id": "tenant-a"}})


def test_runtime_pipeline_enforces_tenant_action_limit() -> None:
    pipeline = RuntimePipeline(
        policy_engine=PolicyEngine(Policy()),
        budget_manager=BudgetManager(max_budget=100.0),
        sandbox_runner=SandboxRunner(),
        approval_queue=ApprovalQueue(),
        max_actions_per_tenant=1,
    )
    action = AgentAction(tool_name="noop", category="default", handler=lambda: "ok", args=(), kwargs={}, tenant_id="tenant-a")
    assert pipeline.execute(action) == "ok"
    with pytest.raises(Exception):
        pipeline.execute(action)


def test_worker_rejects_disallowed_tenant() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=1)
    queue.enqueue_task({"task_id": "x", "name": "task", "metadata": {"tenant_id": "tenant-b"}})
    worker = AgentWorker(
        worker_id="w1",
        queue=queue,
        event_bus=EventBus(),
        task_handler=_Handler(),
        tenant_allowlist={"tenant-a"},
    )

    assert worker.process_once() is True
    assert queue.dead_letter_size() == 1
