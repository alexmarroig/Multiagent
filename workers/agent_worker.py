"""Worker runtime for distributed task execution and horizontal scale-out."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from communication.event_bus import Event, EventBus
from core.task_queue import DistributedTaskQueue, QueueTask


class TaskHandler(Protocol):
    def execute(self, task: QueueTask) -> dict[str, Any]: ...


class ResultStore(Protocol):
    def save_result(self, task: QueueTask, result: dict[str, Any]) -> None: ...


@dataclass(slots=True)
class WorkerTelemetry:
    worker_id: str
    started_at: float = field(default_factory=time.time)
    processed_tasks: int = 0
    failed_tasks: int = 0


class InMemoryResultStore:
    def __init__(self) -> None:
        self._results: dict[str, dict[str, Any]] = {}

    def save_result(self, task: QueueTask, result: dict[str, Any]) -> None:
        self._results[task.task_id] = result

    def to_json(self) -> str:
        return json.dumps(self._results)


class AgentWorker:
    """Long-running worker that polls queue, executes tasks, and publishes completion events."""

    def __init__(
        self,
        *,
        worker_id: str,
        queue: DistributedTaskQueue,
        event_bus: EventBus,
        task_handler: TaskHandler,
        result_store: ResultStore | None = None,
        poll_interval_seconds: float = 0.2,
    ) -> None:
        self.worker_id = worker_id
        self.queue = queue
        self.event_bus = event_bus
        self.task_handler = task_handler
        self.result_store = result_store or InMemoryResultStore()
        self.poll_interval_seconds = max(0.01, poll_interval_seconds)
        self.telemetry = WorkerTelemetry(worker_id=worker_id)
        self._running = False
        self._thread: threading.Thread | None = None

    def process_once(self) -> bool:
        task = self.queue.dequeue_task(timeout_seconds=1)
        if task is None:
            return False

        self.event_bus.publish_event(Event(topic="worker.task_started", payload={"worker_id": self.worker_id, "task_id": task.task_id}))
        try:
            result = self.task_handler.execute(task)
            self.result_store.save_result(task, result)
            self.queue.acknowledge_task(task)
            self.telemetry.processed_tasks += 1
            self.event_bus.report_completion(task_id=task.task_id, worker_id=self.worker_id, result=result)
        except Exception as exc:  # noqa: BLE001
            self.telemetry.failed_tasks += 1
            self.event_bus.publish_event(
                Event(
                    topic="worker.task_failed",
                    payload={"worker_id": self.worker_id, "task_id": task.task_id, "error": str(exc)},
                )
            )
        return True

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            processed = self.process_once()
            if not processed:
                time.sleep(self.poll_interval_seconds)

    def start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self.run_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)


class WorkerPool:
    """Utility to run many worker instances, enabling horizontal scaling."""

    def __init__(self, workers: list[AgentWorker]) -> None:
        self.workers = workers

    def start(self) -> None:
        for worker in self.workers:
            worker.start_background()

    def stop(self) -> None:
        for worker in self.workers:
            worker.stop()
