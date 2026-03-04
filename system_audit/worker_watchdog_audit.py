from __future__ import annotations

from communication.event_bus import EventBus
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from workers.agent_worker import AgentWorker
from workers.watchdog import WorkerWatchdog


class _NoopHandler:
    def execute(self, task):
        return {"success": True, "task_id": task.task_id}


def run_audit() -> dict[str, object]:
    name = "Worker Watchdog"
    try:
        queue = DistributedTaskQueue(InMemoryQueueBackend())
        bus = EventBus()
        watchdog = WorkerWatchdog(
            queue=queue,
            event_bus=bus,
            worker_factory=lambda wid: AgentWorker(worker_id=wid, queue=queue, event_bus=bus, task_handler=_NoopHandler()),
            worker_timeout_seconds=0.01,
        )
        worker = AgentWorker(worker_id="w1", queue=queue, event_bus=bus, task_handler=_NoopHandler())
        watchdog.register_worker(worker)
        watchdog.monitor_once()
        status = "OK" if len(watchdog._workers) >= 1 else "FAILED"
        return {"name": name, "status": status, "details": {"workers_registered": len(watchdog._workers)}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
