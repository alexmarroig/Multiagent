"""Task queue with dynamic spawning and delegation support."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class QueuedTask:
    task_id: str
    agent_id: str
    description: str
    payload: dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    def __init__(self) -> None:
        self._queue: deque[QueuedTask] = deque()

    def enqueue(self, task: QueuedTask) -> None:
        self._queue.append(task)

    def dequeue(self) -> QueuedTask | None:
        if not self._queue:
            return None
        return self._queue.popleft()

    def __len__(self) -> int:
        return len(self._queue)
