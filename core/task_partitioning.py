"""Queue partitioning by tenant, goal, and priority to reduce contention."""

from __future__ import annotations

from dataclasses import dataclass

from core.task_queue import DistributedTaskQueue, QueueTask


@dataclass(slots=True)
class TaskPartition:
    tenant_id: str
    goal_id: str
    priority: int

    @property
    def key(self) -> str:
        band = "high" if self.priority <= 20 else "normal" if self.priority <= 70 else "low"
        return f"tenant:{self.tenant_id}|goal:{self.goal_id}|priority:{band}"


class PartitionedTaskQueue:
    """Thin wrapper around DistributedTaskQueue with deterministic partition routing."""

    def __init__(self, queue: DistributedTaskQueue) -> None:
        self.queue = queue

    def partition_for(self, task: QueueTask) -> TaskPartition:
        tenant_id = str(task.metadata.get("tenant_id", "default"))
        goal_id = str(task.metadata.get("goal_id", "general"))
        return TaskPartition(tenant_id=tenant_id, goal_id=goal_id, priority=task.priority)

    def enqueue(self, task: QueueTask) -> QueueTask:
        partition = self.partition_for(task)
        task.metadata["partition"] = partition.key
        return self.queue.enqueue_task(task)

    def dequeue_for_worker(self, subscriptions: set[str], timeout_seconds: int = 1) -> QueueTask | None:
        # Simple selective consume loop; tasks outside subscription are re-queued.
        for _ in range(max(1, len(subscriptions) * 2)):
            task = self.queue.dequeue_task(timeout_seconds=timeout_seconds)
            if task is None:
                return None
            partition = str(task.metadata.get("partition", ""))
            if partition in subscriptions:
                return task
            self.queue.enqueue_task(task)
            self.queue.acknowledge_task(task)
        return None
