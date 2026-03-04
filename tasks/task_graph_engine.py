"""Distributed task graph engine with dependency resolution and scheduling support."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from heapq import heappop, heappush
from typing import Any

from communication.event_bus import Event, EventBus
from core.task_queue import DistributedTaskQueue, QueueTask
from governance.human_validation import HumanValidationController


@dataclass(slots=True)
class GraphTask:
    task_id: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    dependencies: set[str] = field(default_factory=set)
    priority: int = 50
    status: str = "pending"
    parent_task_id: str | None = None
    depth: int = 0


@dataclass(slots=True)
class TaskGraphSafetyLimits:
    max_total_tasks: int = 200
    max_subtasks_per_task: int = 20
    max_task_depth: int = 4
    max_parallel_tasks: int = 32


class TaskGraphEngine:
    """Converts high-level plans into executable queue tasks with dependency-aware parallelism."""

    def __init__(
        self,
        queue: DistributedTaskQueue,
        *,
        safety_limits: TaskGraphSafetyLimits | None = None,
        event_bus: EventBus | None = None,
        human_validation: HumanValidationController | None = None,
    ) -> None:
        self.queue = queue
        self.safety_limits = safety_limits or TaskGraphSafetyLimits()
        self.event_bus = event_bus
        self.human_validation = human_validation
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
        parent_task_id: str | None = None,
    ) -> GraphTask:
        depth = self._resolve_depth(parent_task_id)
        self._enforce_safety_limits(task_id=task_id, parent_task_id=parent_task_id, depth=depth)
        task = GraphTask(
            task_id=task_id,
            name=name,
            payload=payload or {},
            dependencies=set(dependencies or []),
            priority=priority,
            parent_task_id=parent_task_id,
            depth=depth,
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
            if not self.queue.can_schedule_new_tasks():
                break
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
                    parent_task_id=task_id,
                )
        for child_id in self._children.get(task_id, set()):
            child = self._tasks[child_id]
            if child.status == "pending" and self._dependencies_satisfied(child):
                heappush(self._ready, (child.priority, child.task_id))

    def _dependencies_satisfied(self, task: GraphTask) -> bool:
        return all(self._tasks.get(dep) and self._tasks[dep].status == "completed" for dep in task.dependencies)

    def _resolve_depth(self, parent_task_id: str | None) -> int:
        if parent_task_id is None:
            return 0
        parent = self._tasks.get(parent_task_id)
        return (parent.depth + 1) if parent else 1

    def _active_task_count(self) -> int:
        return sum(1 for task in self._tasks.values() if task.status in {"pending", "queued"})

    def _enforce_safety_limits(self, *, task_id: str, parent_task_id: str | None, depth: int) -> None:
        limits = self.safety_limits
        checks = [
            (len(self._tasks) + 1 > limits.max_total_tasks, "max_total_tasks", limits.max_total_tasks, len(self._tasks) + 1),
            (
                parent_task_id is not None
                and len(self._children.get(parent_task_id, set())) + 1 > limits.max_subtasks_per_task,
                "max_subtasks_per_task",
                limits.max_subtasks_per_task,
                len(self._children.get(parent_task_id, set())) + 1 if parent_task_id else 0,
            ),
            (depth > limits.max_task_depth, "max_task_depth", limits.max_task_depth, depth),
            (
                self._active_task_count() + 1 > limits.max_parallel_tasks,
                "max_parallel_tasks",
                limits.max_parallel_tasks,
                self._active_task_count() + 1,
            ),
        ]
        for exceeded, limit_name, limit_value, observed_value in checks:
            if exceeded:
                self._handle_limit_exceeded(
                    task_id=task_id,
                    limit_name=limit_name,
                    limit_value=limit_value,
                    observed_value=observed_value,
                    parent_task_id=parent_task_id,
                )
                return

    def _handle_limit_exceeded(
        self,
        *,
        task_id: str,
        limit_name: str,
        limit_value: int,
        observed_value: int,
        parent_task_id: str | None,
    ) -> None:
        payload = {
            "task_id": task_id,
            "parent_task_id": parent_task_id,
            "limit_name": limit_name,
            "limit_value": limit_value,
            "observed_value": observed_value,
            "action": "task_creation_blocked",
        }
        if self.event_bus is not None:
            self.event_bus.publish_event(Event(topic="task_graph.limit_exceeded", payload=payload))

        if self.human_validation is not None:
            self.human_validation.request_approval(
                token=f"task_graph:{limit_name}:{task_id}",
                reason=f"{limit_name}_exceeded",
            )
