from __future__ import annotations

import pytest

from communication.durable_event_bus import DurableEventBus, Event
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


def test_runtime_pipeline_enforces_tool_invocation_limit() -> None:
    pipeline = RuntimePipeline(
        policy_engine=PolicyEngine(Policy()),
        budget_manager=BudgetManager(max_budget=100.0),
        sandbox_runner=SandboxRunner(),
        approval_queue=ApprovalQueue(),
        max_actions_per_tenant=10,
        max_tool_invocations_per_tenant={"expensive_tool": 1},
    )
    action = AgentAction(
        tool_name="expensive_tool",
        category="default",
        handler=lambda: "ok",
        args=(),
        kwargs={},
        tenant_id="tenant-a",
    )
    assert pipeline.execute(action) == "ok"
    with pytest.raises(RuntimeError, match="Tool invocation limit exceeded"):
        pipeline.execute(action)


def test_worker_quarantines_flapping_tenant() -> None:
    class _FailHandler:
        def execute(self, task: QueueTask) -> dict:
            raise RuntimeError("boom")

    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=1)
    queue.enqueue_task({"task_id": "x", "name": "task", "metadata": {"tenant_id": "tenant-z"}})
    queue.enqueue_task({"task_id": "y", "name": "task", "metadata": {"tenant_id": "tenant-z"}})
    worker = AgentWorker(
        worker_id="w1",
        queue=queue,
        event_bus=EventBus(),
        task_handler=_FailHandler(),
        max_tenant_failures_before_quarantine=1,
    )

    assert worker.process_once() is True
    assert worker.process_once() is True
    assert queue.dead_letter_size() == 2


def test_durable_event_bus_deduplicates_event_ids() -> None:
    bus = DurableEventBus()
    seen: list[str] = []
    bus.subscribe("topic", lambda event: seen.append(event.event_id or ""))

    event = Event(topic="topic", payload={"x": 1}, event_id="evt-1")
    first = bus.publish_event(event)
    second = bus.publish_event(event)

    assert first == "evt-1"
    assert second == "evt-1"
    assert seen == ["evt-1"]


def test_runtime_pipeline_blocks_consecutive_same_tool_loop() -> None:
    pipeline = RuntimePipeline(
        policy_engine=PolicyEngine(Policy()),
        budget_manager=BudgetManager(max_budget=100.0),
        sandbox_runner=SandboxRunner(),
        approval_queue=ApprovalQueue(),
        max_actions_per_tenant=10,
        max_consecutive_tool_invocations=2,
    )
    action = AgentAction(tool_name="planner", category="default", handler=lambda: "ok", args=(), kwargs={}, tenant_id="tenant-a")
    assert pipeline.execute(action) == "ok"
    assert pipeline.execute(action) == "ok"
    with pytest.raises(RuntimeError, match="Consecutive tool invocation limit exceeded"):
        pipeline.execute(action)


def test_queue_rejects_hard_saturation() -> None:
    queue = DistributedTaskQueue(
        InMemoryQueueBackend(),
        queue_high_watermark=2,
        queue_low_watermark=1,
        saturation_reject_ratio=1.0,
    )
    queue.enqueue_task({"task_id": "t1", "name": "a"})
    queue.enqueue_task({"task_id": "t2", "name": "a"})
    with pytest.raises(OverflowError, match="hard saturation"):
        queue.enqueue_task({"task_id": "t3", "name": "a"})


def test_durable_event_bus_rate_limits_hot_topic() -> None:
    bus = DurableEventBus(max_events_per_second_per_topic=1)
    bus.publish("topic", {"x": 1})
    with pytest.raises(RuntimeError, match="rate limited"):
        bus.publish("topic", {"x": 2})
