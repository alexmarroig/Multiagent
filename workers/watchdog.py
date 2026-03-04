"""Worker watchdog for heartbeats, task timeouts, and resource exhaustion handling."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from agentos.communication.event_bus import Event, EventBus
from agentos.core.task_queue import DistributedTaskQueue, QueueTask
from workers.agent_worker import AgentWorker
from agentos.monitoring.structured_logging import log_event

ResourceProbe = Callable[[AgentWorker], dict[str, Any] | None]
WorkerFactory = Callable[[str], AgentWorker]


@dataclass(slots=True)
class WorkerState:
    worker: AgentWorker
    last_heartbeat: float
    active_task: QueueTask | None = None
    active_task_started_at: float | None = None


class WorkerWatchdog:
    """Monitors active workers and remediates timeout, heartbeat, and resource incidents."""

    def __init__(
        self,
        *,
        queue: DistributedTaskQueue,
        event_bus: EventBus,
        worker_factory: WorkerFactory,
        worker_timeout_seconds: float = 30.0,
        task_timeout_seconds: float = 120.0,
        monitor_interval_seconds: float = 1.0,
        resource_probe: ResourceProbe | None = None,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.queue = queue
        self.event_bus = event_bus
        self.worker_factory = worker_factory
        self.worker_timeout_seconds = max(0.5, worker_timeout_seconds)
        self.task_timeout_seconds = max(0.5, task_timeout_seconds)
        self.monitor_interval_seconds = max(0.1, monitor_interval_seconds)
        self.resource_probe = resource_probe
        self.time_fn = time_fn or time.time
        self._workers: dict[str, WorkerState] = {}
        self._running = False
        self._thread: threading.Thread | None = None

        self.event_bus.subscribe_event("worker.heartbeat", self._on_heartbeat)
        self.event_bus.subscribe_event("worker.task_started", self._on_task_started)
        self.event_bus.subscribe_event("worker.task_completed", self._on_task_completed)
        self.event_bus.subscribe_event("worker.task_failed", self._on_task_completed)

    def register_worker(self, worker: AgentWorker) -> None:
        self._workers[worker.worker_id] = WorkerState(worker=worker, last_heartbeat=self.time_fn())

    def monitor_once(self) -> None:
        now = self.time_fn()
        for worker_id in list(self._workers.keys()):
            state = self._workers.get(worker_id)
            if state is None:
                continue

            issue = self._detect_issue(state=state, now=now)
            if issue is None:
                continue
            self._recover(worker_id=worker_id, issue=issue)

    def run_forever(self) -> None:
        self._running = True
        while self._running:
            self.monitor_once()
            time.sleep(self.monitor_interval_seconds)

    def start_background(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self.run_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _detect_issue(self, *, state: WorkerState, now: float) -> dict[str, Any] | None:
        if now - state.last_heartbeat > self.worker_timeout_seconds:
            return {"type": "heartbeat_timeout", "last_heartbeat": state.last_heartbeat}

        if state.active_task and state.active_task_started_at and now - state.active_task_started_at > self.task_timeout_seconds:
            return {
                "type": "task_timeout",
                "task_id": state.active_task.task_id,
                "task_started_at": state.active_task_started_at,
            }

        if self.resource_probe:
            probe_result = self.resource_probe(state.worker)
            if probe_result:
                return {"type": "resource_exhaustion", "details": probe_result}

        return None

    def _recover(self, *, worker_id: str, issue: dict[str, Any]) -> None:
        state = self._workers.pop(worker_id, None)
        if state is None:
            return

        state.worker.stop()
        requeued_task: str | None = None
        if state.active_task is not None:
            self.queue.enqueue_task(state.active_task)
            requeued_task = state.active_task.task_id

        replacement_id = f"{worker_id}-replacement-{uuid.uuid4().hex[:6]}"
        replacement = self.worker_factory(replacement_id)
        replacement.start_background()
        self._workers[replacement.worker_id] = WorkerState(worker=replacement, last_heartbeat=self.time_fn())

        log_event(logging.getLogger(__name__), component="watchdog", event="worker_recovery", severity="warning", worker_id=worker_id, issue=issue)
        self.event_bus.publish_event(
            Event(
                topic="system.alert",
                payload={
                    "severity": "critical",
                    "category": issue.get("type", "worker_incident"),
                    "worker_id": worker_id,
                    "requeued_task_id": requeued_task,
                    "replacement_worker_id": replacement.worker_id,
                    "issue": issue,
                },
            )
        )

    def _on_heartbeat(self, event: Event) -> None:
        worker_id = event.payload.get("worker_id")
        if not worker_id or worker_id not in self._workers:
            return
        timestamp = float(event.payload.get("timestamp", self.time_fn()))
        self._workers[worker_id].last_heartbeat = timestamp

    def _on_task_started(self, event: Event) -> None:
        worker_id = event.payload.get("worker_id")
        if not worker_id or worker_id not in self._workers:
            return

        raw_task = event.payload.get("task")
        if isinstance(raw_task, dict):
            task = QueueTask(
                task_id=raw_task.get("task_id", event.payload.get("task_id", "")),
                name=raw_task.get("name", "task"),
                payload=raw_task.get("payload", {}),
                priority=int(raw_task.get("priority", 50)),
                dependencies=list(raw_task.get("dependencies", [])),
                metadata=dict(raw_task.get("metadata", {})),
                created_at=float(raw_task.get("created_at", self.time_fn())),
            )
        else:
            task_id = event.payload.get("task_id", "unknown")
            task = QueueTask(task_id=task_id, name="task")

        state = self._workers[worker_id]
        state.active_task = task
        state.active_task_started_at = self.time_fn()

    def _on_task_completed(self, event: Event) -> None:
        worker_id = event.payload.get("worker_id")
        if not worker_id or worker_id not in self._workers:
            return

        state = self._workers[worker_id]
        state.active_task = None
        state.active_task_started_at = None
