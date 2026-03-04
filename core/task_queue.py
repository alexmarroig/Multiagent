"""Distributed task queue abstraction with Redis-backed and in-memory implementations."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class QueueTask:
    """Serializable task payload exchanged between planner and workers."""

    task_id: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 50
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_json(self) -> str:
        return json.dumps(
            {
                "task_id": self.task_id,
                "name": self.name,
                "payload": self.payload,
                "priority": self.priority,
                "dependencies": self.dependencies,
                "metadata": self.metadata,
                "created_at": self.created_at,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> "QueueTask":
        data = json.loads(raw)
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            payload=data.get("payload", {}),
            priority=int(data.get("priority", 50)),
            dependencies=list(data.get("dependencies", [])),
            metadata=dict(data.get("metadata", {})),
            created_at=float(data.get("created_at", time.time())),
        )


class QueueBackend(Protocol):
    def push(self, queue_name: str, item: str) -> None: ...

    def pop(self, queue_name: str, timeout_seconds: int = 1) -> str | None: ...

    def ack(self, processing_queue_name: str, item: str) -> None: ...


class InMemoryQueueBackend:
    """Simple fallback backend for local/dev use."""

    def __init__(self) -> None:
        from collections import deque

        self._queues: dict[str, deque[str]] = {}

    def _get(self, queue_name: str):
        from collections import deque

        return self._queues.setdefault(queue_name, deque())

    def push(self, queue_name: str, item: str) -> None:
        self._get(queue_name).append(item)

    def pop(self, queue_name: str, timeout_seconds: int = 1) -> str | None:
        queue = self._get(queue_name)
        if queue:
            return queue.popleft()
        return None

    def ack(self, processing_queue_name: str, item: str) -> None:
        queue = self._get(processing_queue_name)
        try:
            queue.remove(item)
        except ValueError:
            return


class RedisQueueBackend:
    """Redis backend using BRPOPLPUSH semantics for at-least-once delivery."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisQueueBackend":
        try:
            import redis
        except ModuleNotFoundError as exc:  # pragma: no cover - runtime dependency check
            raise RuntimeError("redis package is required for RedisQueueBackend") from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True))

    def push(self, queue_name: str, item: str) -> None:
        self.redis.lpush(queue_name, item)

    def pop(self, queue_name: str, timeout_seconds: int = 1) -> str | None:
        processing = f"{queue_name}:processing"
        return self.redis.brpoplpush(queue_name, processing, timeout=timeout_seconds)

    def ack(self, processing_queue_name: str, item: str) -> None:
        self.redis.lrem(processing_queue_name, count=1, value=item)


class DistributedTaskQueue:
    """Distributed task queue that decouples planning from execution."""

    def __init__(self, backend: QueueBackend, queue_name: str = "agentos:tasks") -> None:
        self.backend = backend
        self.queue_name = queue_name

    @property
    def processing_queue_name(self) -> str:
        return f"{self.queue_name}:processing"

    def enqueue_task(self, task: QueueTask | dict[str, Any]) -> QueueTask:
        if isinstance(task, dict):
            task = QueueTask(
                task_id=task.get("task_id", f"task-{uuid.uuid4().hex[:12]}"),
                name=task.get("name", task.get("description", "task")),
                payload=task.get("payload", {}),
                priority=int(task.get("priority", 50)),
                dependencies=list(task.get("dependencies", [])),
                metadata=task.get("metadata", {}),
            )
        self.backend.push(self.queue_name, task.to_json())
        return task

    def dequeue_task(self, timeout_seconds: int = 1) -> QueueTask | None:
        raw = self.backend.pop(self.queue_name, timeout_seconds=timeout_seconds)
        if raw is None:
            return None
        return QueueTask.from_json(raw)

    def acknowledge_task(self, task: QueueTask) -> None:
        self.backend.ack(self.processing_queue_name, task.to_json())
