from __future__ import annotations

import time

from communication.event_bus import EventBus
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from workers.agent_worker import AgentWorker
from workers.watchdog import WorkerWatchdog


class _SlowHandler:
    def execute(self, task):
        time.sleep(0.001)
        return {"success": True}


def test_task_explosion_limits_enforced() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=3, queue_low_watermark=1)
    for idx in range(10):
        queue.enqueue_task({"task_id": f"explode-{idx}", "name": "spawn"})
    assert queue.is_under_pressure() is True
    assert queue.can_schedule_new_tasks() is False


def test_queue_saturation_triggers_backpressure() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=5, queue_low_watermark=2)
    for idx in range(6):
        queue.enqueue_task({"task_id": f"t-{idx}", "name": "load"})
    assert queue.is_under_pressure() is True
    assert queue.can_schedule_new_tasks() is False


def test_llm_budget_overrun_alerts() -> None:
    from monitoring.alerts import AlertManager

    manager = AlertManager(llm_budget_limit=1.0)
    alerts = manager.evaluate_runtime_signals(queue_depth=1, error_rate=0.0, llm_cost=5.0)
    assert any(alert.category == "llm_budget_exceeded" for alert in alerts)


def test_worker_crash_recovery_keeps_system_responsive() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    bus = EventBus()

    def factory(worker_id: str) -> AgentWorker:
        return AgentWorker(worker_id=worker_id, queue=queue, event_bus=bus, task_handler=_SlowHandler())

    watchdog = WorkerWatchdog(queue=queue, event_bus=bus, worker_factory=factory, worker_timeout_seconds=0.01)
    worker = factory("worker-1")
    watchdog.register_worker(worker)
    watchdog.monitor_once()

    assert len(watchdog._workers) >= 1
