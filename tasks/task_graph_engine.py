"""Distributed task graph engine with dependency resolution and scheduling support."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Any

from core.task_queue import DistributedTaskQueue, QueueTask


@dataclass(slots=True)
class GraphTask:
    task_id: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    dependencies: set[str] = field(default_factory=set)
    priority: int = 50
    status: str = "pending"


class TaskGraphEngine:
    """Converts high-level plans into executable queue tasks with dependency-aware parallelism."""

    def __init__(self, queue: DistributedTaskQueue) -> None:
        self.queue = queue
        self._tasks: dict[str, GraphTask] = {}
        self._children: dict[str, set[str]] = {}
        self._ready: list[tuple[int, str]] = []

    def add_task(
        self,
        *,
        task_id: str,
        name: str,
        payload: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        priority: int = 50,
    ) -> GraphTask:
        task = GraphTask(
            task_id=task_id,
            name=name,
            payload=payload or {},
            dependencies=set(dependencies or []),
            priority=priority,
        )
        self._tasks[task_id] = task
        for dep in task.dependencies:
            self._children.setdefault(dep, set()).add(task_id)
        if self._dependencies_satisfied(task):
            heappush(self._ready, (task.priority, task_id))
        return task

    def ingest_plan(self, plan: list[dict[str, Any]]) -> list[GraphTask]:
        tasks = []
        for item in plan:
            tasks.append(
                self.add_task(
                    task_id=item.get("task_id", f"task-{uuid.uuid4().hex[:10]}"),
                    name=item.get("name", item.get("description", "planned-task")),
                    payload=item.get("payload", {}),
                    dependencies=item.get("dependencies", []),
                    priority=int(item.get("priority", 50)),
                )
            )
        return tasks

    def schedule_ready_tasks(self, limit: int | None = None) -> list[QueueTask]:
        scheduled: list[QueueTask] = []
        while self._ready and (limit is None or len(scheduled) < limit):
            _, task_id = heappop(self._ready)
            task = self._tasks[task_id]
            if task.status != "pending" or not self._dependencies_satisfied(task):
                continue
            queue_task = QueueTask(
                task_id=task.task_id,
                name=task.name,
                payload=task.payload,
                priority=task.priority,
                dependencies=sorted(task.dependencies),
                metadata={"origin": "task_graph_engine"},
            )
            self.queue.enqueue_task(queue_task)
            task.status = "queued"
            scheduled.append(queue_task)
        return scheduled

    def mark_task_completed(self, task_id: str, spawned_tasks: list[dict[str, Any]] | None = None) -> None:
        task = self._tasks[task_id]
        task.status = "completed"
        if spawned_tasks:
            for spawned in spawned_tasks:
                self.add_task(
                    task_id=spawned.get("task_id", f"task-{uuid.uuid4().hex[:10]}"),
                    name=spawned.get("name", "spawned-task"),
                    payload=spawned.get("payload", {}),
                    dependencies=spawned.get("dependencies", [task_id]),
                    priority=int(spawned.get("priority", task.priority)),
                )
        for child_id in self._children.get(task_id, set()):
            child = self._tasks[child_id]
            if child.status == "pending" and self._dependencies_satisfied(child):
                heappush(self._ready, (child.priority, child.task_id))

    def _dependencies_satisfied(self, task: GraphTask) -> bool:
        return all(self._tasks.get(dep) and self._tasks[dep].status == "completed" for dep in task.dependencies)
