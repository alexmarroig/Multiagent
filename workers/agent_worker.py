"""Worker runtime for distributed task execution and horizontal scale-out."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from communication.event_bus import Event, EventBus
from core.task_queue import DistributedTaskQueue, QueueTask
from core.retry_engine import RetryEngine, get_default_retry_engine
from monitoring.runtime_metrics import runtime_metrics
from monitoring.tracing import get_tracer


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
        heartbeat_interval_seconds: float = 1.0,
        retry_engine: RetryEngine | None = None,
        max_batch_size: int = 4,
        tenant_allowlist: set[str] | None = None,
        max_consecutive_failures: int = 25,
        max_tenant_failures_before_quarantine: int = 5,
    ) -> None:
        self.worker_id = worker_id
        self.queue = queue
        self.event_bus = event_bus
        self.task_handler = task_handler
        self.result_store = result_store or InMemoryResultStore()
        self.poll_interval_seconds = max(0.01, poll_interval_seconds)
        self.heartbeat_interval_seconds = max(0.05, heartbeat_interval_seconds)
        self.telemetry = WorkerTelemetry(worker_id=worker_id)
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_heartbeat = 0.0
        self._tracer = get_tracer()
        self.retry_engine = retry_engine or get_default_retry_engine()
        self.max_batch_size = max(1, max_batch_size)
        self.tenant_allowlist = tenant_allowlist
        self.max_consecutive_failures = max(1, max_consecutive_failures)
        self.max_tenant_failures_before_quarantine = max(1, max_tenant_failures_before_quarantine)
        self._consecutive_failures = 0
        self._tenant_failures: dict[str, int] = {}
        self._tenant_quarantine: set[str] = set()

    def _emit_heartbeat(self) -> None:
        now = time.time()
        if now - self._last_heartbeat < self.heartbeat_interval_seconds:
            return
        self._last_heartbeat = now
        self.event_bus.publish_event(
            Event(topic="worker.heartbeat", payload={"worker_id": self.worker_id, "timestamp": now})
        )

    def process_once(self) -> bool:
        task = self.queue.dequeue_task(timeout_seconds=1)
        if task is None:
            return False

        tenant_id = str(task.metadata.get("tenant_id", "default"))
        if self.tenant_allowlist is not None and tenant_id not in self.tenant_allowlist:
            self.queue.fail_task(task, error=f"tenant_not_allowed:{tenant_id}")
            runtime_metrics.inc("worker.tasks_rejected")
            return True

        if tenant_id in self._tenant_quarantine:
            self.queue.fail_task(task, error=f"tenant_quarantined:{tenant_id}")
            runtime_metrics.inc("worker.tasks_rejected")
            return True

        with self._tracer.start_span("agent.execution", kind="agent_execution", attributes={"worker_id": self.worker_id, "task_id": task.task_id}):
            self.event_bus.publish_event(
                Event(
                    topic="worker.task_started",
                    payload={"worker_id": self.worker_id, "task_id": task.task_id, "task": asdict(task)},
                )
            )
            try:
                result = self.retry_engine.execute(
                    "task_execution",
                    self.task_handler.execute,
                    task,
                    context={"worker_id": self.worker_id, "task_id": task.task_id, "task_name": task.name},
                )
                self.result_store.save_result(task, result)
                self._consecutive_failures = 0
                self._tenant_failures[tenant_id] = 0
                self.queue.acknowledge_task(task)
                self.telemetry.processed_tasks += 1
                self.event_bus.report_completion(task_id=task.task_id, worker_id=self.worker_id, result=result)
                runtime_metrics.inc("worker.tasks_processed")
            except Exception as exc:  # noqa: BLE001
                self.telemetry.failed_tasks += 1
                self._consecutive_failures += 1
                tenant_failures = self._tenant_failures.get(tenant_id, 0) + 1
                self._tenant_failures[tenant_id] = tenant_failures
                if tenant_failures >= self.max_tenant_failures_before_quarantine:
                    self._tenant_quarantine.add(tenant_id)
                    runtime_metrics.inc("worker.tenant_quarantined")
                self.queue.fail_task(task, error=str(exc), exc=exc)
                runtime_metrics.inc("worker.tasks_failed")
                self.event_bus.publish_event(
                    Event(
                        topic="worker.task_failed",
                        payload={"worker_id": self.worker_id, "task_id": task.task_id, "error": str(exc)},
                    )
                )
        return True


    def process_batch(self) -> int:
        processed = 0
        for _ in range(self.max_batch_size):
            if not self.process_once():
                break
            processed += 1
        runtime_metrics.set_gauge("worker.utilization", float(processed / self.max_batch_size))
        return processed

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            if self._consecutive_failures >= self.max_consecutive_failures:
                runtime_metrics.inc("worker.circuit_breaker_tripped")
                self._running = False
                break
            self._emit_heartbeat()
            processed = self.process_batch()
            if self.queue.is_under_pressure():
                time.sleep(self.poll_interval_seconds * 2)
                continue
            if processed == 0:
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
