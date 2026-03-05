"""Stateless worker implementation backed by external stores and event bus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from core.task_queue import QueueTask


class TaskStore(Protocol):
    def save_result(self, task_id: str, result: dict[str, Any]) -> None: ...


class MemoryStore(Protocol):
    def append_memory(self, key: str, value: dict[str, Any]) -> None: ...


class EventBus(Protocol):
    def publish(self, topic: str, payload: dict[str, Any]) -> None: ...


@dataclass(slots=True)
class StatelessWorker:
    """Worker keeps no local durable state; all state externalized."""

    worker_id: str
    task_store: TaskStore
    memory_store: MemoryStore
    event_bus: EventBus

    def process(self, task: QueueTask) -> dict[str, Any]:
        result = {
            "task_id": task.task_id,
            "worker_id": self.worker_id,
            "status": "completed",
            "output": f"processed:{task.name}",
        }
        self.task_store.save_result(task.task_id, result)
        self.memory_store.append_memory(task.metadata.get("goal_id", "default"), result)
        self.event_bus.publish("worker.task.completed", result)
        return result
