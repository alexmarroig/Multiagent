from __future__ import annotations

from dataclasses import asdict
from typing import Any

from agentos.communication.event_bus import Event, EventBus
from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask
from workers.agent_worker import AgentWorker
from workers.watchdog import WorkerWatchdog


class NoopHandler:
    def execute(self, task: QueueTask) -> dict[str, Any]:
        return {"ok": True, "task_id": task.task_id}


class DummyWorker:
    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.stopped = False
        self.started = False

    def stop(self) -> None:
        self.stopped = True

    def start_background(self) -> None:
        self.started = True


def test_watchdog_replaces_worker_and_alerts_on_task_timeout():
    queue = DistributedTaskQueue(backend=InMemoryQueueBackend(), queue_name="watchdog:task-timeout")
    event_bus = EventBus()
    now = 1000.0
    replacements: list[DummyWorker] = []

    def time_fn() -> float:
        return now

    def worker_factory(worker_id: str) -> DummyWorker:
        worker = DummyWorker(worker_id)
        replacements.append(worker)
        return worker

    worker = DummyWorker("worker-a")
    watchdog = WorkerWatchdog(
        queue=queue,
        event_bus=event_bus,
        worker_factory=worker_factory,
        worker_timeout_seconds=60,
        task_timeout_seconds=5,
        time_fn=time_fn,
    )
    watchdog.register_worker(worker)

    task = QueueTask(task_id="task-1", name="long-task")
    event_bus.publish_event(
        Event(topic="worker.task_started", payload={"worker_id": "worker-a", "task_id": task.task_id, "task": asdict(task)})
    )

    alerts: list[dict[str, Any]] = []
    event_bus.subscribe_event("system.alert", lambda e: alerts.append(e.payload))

    now = 1010.0
    watchdog.monitor_once()

    assert worker.stopped is True
    assert len(replacements) == 1 and replacements[0].started is True
    assert alerts and alerts[0]["category"] == "task_timeout"
    requeued = queue.dequeue_task(timeout_seconds=0)
    assert requeued is not None and requeued.task_id == "task-1"


def test_watchdog_replaces_worker_on_resource_exhaustion():
    queue = DistributedTaskQueue(backend=InMemoryQueueBackend(), queue_name="watchdog:resource")
    event_bus = EventBus()
    replacements: list[DummyWorker] = []

    def worker_factory(worker_id: str) -> DummyWorker:
        worker = DummyWorker(worker_id)
        replacements.append(worker)
        return worker

    worker = DummyWorker("worker-b")
    watchdog = WorkerWatchdog(
        queue=queue,
        event_bus=event_bus,
        worker_factory=worker_factory,
        resource_probe=lambda _: {"memory_percent": 98.2},
        worker_timeout_seconds=60,
        task_timeout_seconds=60,
    )
    watchdog.register_worker(worker)

    alerts: list[dict[str, Any]] = []
    event_bus.subscribe_event("system.alert", lambda e: alerts.append(e.payload))

    watchdog.monitor_once()

    assert worker.stopped is True
    assert replacements and replacements[0].started is True
    assert alerts and alerts[0]["category"] == "resource_exhaustion"


def test_agent_worker_emits_heartbeat_event():
    queue = DistributedTaskQueue(backend=InMemoryQueueBackend(), queue_name="watchdog:heartbeat")
    event_bus = EventBus()
    worker = AgentWorker(
        worker_id="worker-heartbeat",
        queue=queue,
        event_bus=event_bus,
        task_handler=NoopHandler(),
        heartbeat_interval_seconds=0.0,
    )

    heartbeats: list[dict[str, Any]] = []
    event_bus.subscribe_event("worker.heartbeat", lambda e: heartbeats.append(e.payload))

    worker._emit_heartbeat()

    assert heartbeats
    assert heartbeats[0]["worker_id"] == "worker-heartbeat"
