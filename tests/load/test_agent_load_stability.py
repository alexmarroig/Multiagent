from __future__ import annotations

import pytest

from agentos.communication.event_bus import EventBus
from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from workers.agent_worker import AgentWorker


class _DeterministicHandler:
    def execute(self, task):
        return {"success": True, "task_id": task.task_id}


@pytest.mark.parametrize("agent_count", [100, 500, 1000])
def test_system_stable_under_large_agent_simulation(agent_count: int) -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=agent_count + 1, queue_low_watermark=1)
    event_bus = EventBus()

    workers = [
        AgentWorker(
            worker_id=f"worker-{idx}",
            queue=queue,
            event_bus=event_bus,
            task_handler=_DeterministicHandler(),
        )
        for idx in range(agent_count)
    ]

    for idx in range(agent_count):
        queue.enqueue_task({"task_id": f"task-{idx}", "name": "load-test", "payload": {"index": idx}})

    processed = sum(1 for worker in workers if worker.process_once())

    assert processed == agent_count
    assert queue.queue_size() == 0
    assert queue.dead_letter_size() == 0
    assert all(worker.telemetry.failed_tasks == 0 for worker in workers)
