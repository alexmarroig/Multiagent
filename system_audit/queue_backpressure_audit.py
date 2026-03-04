from __future__ import annotations

from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend


def run_audit() -> dict[str, object]:
    name = "Queue Backpressure"
    try:
        queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=10, queue_low_watermark=4)
        for idx in range(11):
            queue.enqueue_task({"task_id": f"q-{idx}", "name": "test"})
        paused = queue.is_under_pressure()
        status = "OK" if paused else "FAILED"
        return {
            "name": name,
            "status": status,
            "details": {"queue_size": queue.queue_size(), "scheduling_paused": paused},
        }
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
