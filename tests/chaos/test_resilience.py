from __future__ import annotations

from agentos.communication.event_bus import EventBus
from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask
from memory.vector_memory import VectorMemory
from workers.agent_worker import AgentWorker


class CrashHandler:
    def execute(self, task: QueueTask) -> dict:
        if task.payload.get("crash"):
            raise RuntimeError("worker crash")
        return {"ok": True, "task": task.task_id}


def test_worker_crash_recovers_with_retry_and_dlq() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=2, visibility_timeout_seconds=1)
    queue.enqueue_task({"task_id": "t1", "name": "chaos", "payload": {"crash": True}})
    worker = AgentWorker(worker_id="w1", queue=queue, event_bus=EventBus(), task_handler=CrashHandler())

    worker.process_once()
    assert queue.queue_size() == 1
    worker.process_once()
    assert queue.dead_letter_size() == 1


def test_queue_overload_backpressure() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=3, queue_low_watermark=1)
    for idx in range(5):
        queue.enqueue_task({"task_id": f"t{idx}", "name": "load"})
    assert queue.is_under_pressure() is True


def test_api_failure_does_not_crash_worker() -> None:
    class ApiFailureHandler:
        def execute(self, task: QueueTask) -> dict:
            raise ConnectionError("api unavailable")

    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=1)
    queue.enqueue_task({"task_id": "api-1", "name": "fetch"})
    worker = AgentWorker(worker_id="w-api", queue=queue, event_bus=EventBus(), task_handler=ApiFailureHandler())

    processed = worker.process_once()
    assert processed is True
    assert worker.telemetry.failed_tasks == 1
    assert queue.dead_letter_size() == 1


def test_memory_corruption_recovery() -> None:
    memory = VectorMemory()
    memory.store_knowledge({"id": "k1", "content": "stable"})
    memory._records.append(memory._records[0])  # emulate corruption/duplicate entry
    results = memory.semantic_retrieve("stable", limit=2)
    assert len(results) == 2
