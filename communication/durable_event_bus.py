"""Durable cross-process event streaming built on Redis Streams with consumer groups."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from monitoring.runtime_metrics import runtime_metrics


@dataclass(slots=True)
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str | None = None
    timestamp: float = field(default_factory=time.time)


Subscriber = Callable[[Event], None]


class DurableEventBus:
    """Redis Stream-backed event bus with replay and consumer group support."""

    def __init__(self, redis_client: Any | None = None, *, stream_name: str = "agentos:events") -> None:
        self.redis = redis_client
        self.stream_name = stream_name
        self._local_subscribers: dict[str, list[Subscriber]] = {}

    @classmethod
    def from_url(cls, redis_url: str, *, stream_name: str = "agentos:events") -> "DurableEventBus":
        try:
            import redis
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError("redis package is required for DurableEventBus.from_url") from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True), stream_name=stream_name)

    def subscribe(self, topic: str, callback: Subscriber) -> None:
        self._local_subscribers.setdefault(topic, []).append(callback)

    def subscribe_event(self, topic: str, callback: Subscriber) -> None:
        self.subscribe(topic, callback)

    def publish(self, topic: str, payload: dict[str, Any]) -> str:
        event = Event(topic=topic, payload=payload)
        return self.publish_event(event)

    def publish_event(self, event: Event) -> str:
        message = {"topic": event.topic, "payload": json.dumps(event.payload), "timestamp": str(event.timestamp)}
        if self.redis is not None:
            try:
                message_id = str(self.redis.xadd(self.stream_name, message))
            except Exception:
                runtime_metrics.inc("event_bus.publish_failures")
                raise
        else:
            event.event_id = event.event_id or f"local-{uuid.uuid4().hex}"
            message_id = event.event_id
        self._dispatch_local(Event(topic=event.topic, payload=event.payload, event_id=message_id, timestamp=event.timestamp))
        runtime_metrics.inc("event_bus.published")
        return message_id

    def replay(self, callback: Subscriber, *, topic: str | None = None, from_id: str = "0-0", count: int = 100) -> list[Event]:
        events: list[Event] = []
        if self.redis is None:
            return events
        for message_id, data in self.redis.xrange(self.stream_name, min=from_id, count=count):
            event = Event(topic=data["topic"], payload=json.loads(data["payload"]), event_id=message_id, timestamp=float(data.get("timestamp", time.time())))
            if topic and event.topic != topic:
                continue
            callback(event)
            events.append(event)
        return events

    def ensure_consumer_group(self, group: str, *, start_id: str = "0") -> None:
        if self.redis is None:
            return
        try:
            self.redis.xgroup_create(self.stream_name, group, id=start_id, mkstream=True)
        except Exception as exc:  # noqa: BLE001
            if "BUSYGROUP" not in str(exc):
                raise

    def consume(self, *, group: str, consumer: str, callback: Subscriber, block_ms: int = 1000, count: int = 10) -> int:
        if self.redis is None:
            return 0
        self.ensure_consumer_group(group)
        rows = self.redis.xreadgroup(group, consumer, {self.stream_name: ">"}, count=count, block=block_ms)
        processed = 0
        for _, messages in rows:
            for message_id, data in messages:
                event = Event(topic=data["topic"], payload=json.loads(data["payload"]), event_id=message_id, timestamp=float(data.get("timestamp", time.time())))
                callback(event)
                self.redis.xack(self.stream_name, group, message_id)
                runtime_metrics.inc("event_bus.consumed")
                self._dispatch_local(event)
                processed += 1
        return processed

    def broadcast(self, payload: dict[str, Any]) -> str:
        return self.publish("broadcast", payload)

    def report_completion(self, *, task_id: str, worker_id: str, result: dict[str, Any]) -> None:
        self.publish("worker.task_completed", {"task_id": task_id, "worker_id": worker_id, "result": result})

    def _dispatch_local(self, event: Event) -> None:
        for callback in self._local_subscribers.get(event.topic, []):
            callback(event)
        for callback in self._local_subscribers.get("*", []):
            callback(event)
