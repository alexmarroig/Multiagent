"""Task graph engine with dependencies, dynamic spawning, priorities, and parallel execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from heapq import heappop, heappush
from typing import Any, Callable


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


@dataclass(slots=True)
class TaskNode:
    task_id: str
    description: str
    priority: int = 50
    dependencies: set[str] = field(default_factory=set)
    required_skill: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING


class TaskGraph:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskNode] = {}
        self._ready_heap: list[tuple[int, str]] = []

    def add_task(
        self,
        *,
        task_id: str,
        description: str,
        priority: int = 50,
        dependencies: list[str] | None = None,
        required_skill: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        node = TaskNode(
            task_id=task_id,
            description=description,
            priority=priority,
            dependencies=set(dependencies or []),
            required_skill=required_skill,
            payload=payload or {},
        )
        self._tasks[task_id] = node
        self._refresh_ready(task_id)

    def spawn_task(self, *, parent_task_id: str, task_id: str, description: str, priority: int = 50, payload: dict[str, Any] | None = None, required_skill: str | None = None) -> None:
        self.add_task(
            task_id=task_id,
            description=description,
            priority=priority,
            dependencies=[parent_task_id],
            payload=payload,
            required_skill=required_skill,
        )

    def _refresh_ready(self, task_id: str) -> None:
        task = self._tasks[task_id]
        if task.state != TaskState.PENDING:
            return
        unresolved = [dep for dep in task.dependencies if self._tasks.get(dep, TaskNode(dep, "")).state != TaskState.COMPLETED]
        if not unresolved:
            heappush(self._ready_heap, (task.priority, task.task_id))

    def get_ready_tasks(self, limit: int | None = None) -> list[TaskNode]:
        ready: list[TaskNode] = []
        cap = limit if limit is not None else len(self._ready_heap)
        while self._ready_heap and len(ready) < cap:
            _, task_id = heappop(self._ready_heap)
            task = self._tasks[task_id]
            if task.state == TaskState.PENDING:
                task.state = TaskState.RUNNING
                ready.append(task)
        return ready

    def mark_completed(self, task_id: str) -> None:
        task = self._tasks[task_id]
        task.state = TaskState.COMPLETED
        for node in self._tasks.values():
            self._refresh_ready(node.task_id)

    def execute_parallel(self, worker: Callable[[TaskNode], Any], max_workers: int = 4) -> list[Any]:
        batch = self.get_ready_tasks(limit=max_workers)
        if not batch:
            return []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(worker, batch))

    def pending_count(self) -> int:
        return sum(1 for task in self._tasks.values() if task.state != TaskState.COMPLETED)
