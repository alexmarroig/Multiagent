"""Event bus abstraction for distributed agent communication."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)


Subscriber = Callable[[Event], None]


class EventBus:
    """Pub/sub event bus with publish, subscribe, and broadcast capabilities."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._wildcard_subscribers: list[Subscriber] = []

    def subscribe_event(self, topic: str, callback: Subscriber) -> None:
        if topic == "*":
            self._wildcard_subscribers.append(callback)
        else:
            self._subscribers[topic].append(callback)

    def publish_event(self, event: Event) -> None:
        for callback in self._subscribers.get(event.topic, []):
            callback(event)
        for callback in self._wildcard_subscribers:
            callback(event)

    def broadcast(self, payload: dict[str, Any]) -> None:
        self.publish_event(Event(topic="broadcast", payload=payload))

    def report_completion(self, *, task_id: str, worker_id: str, result: dict[str, Any]) -> None:
        self.publish_event(
            Event(
                topic="worker.task_completed",
                payload={"task_id": task_id, "worker_id": worker_id, "result": result},
            )
        )
