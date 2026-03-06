"""Streaming de eventos em tempo real via Redis Pub/Sub."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import AsyncGenerator

from redis.asyncio import Redis

from models.schemas import AgentEvent
from observability.logging import log_structured

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
logger = logging.getLogger("agentos-orchestrator")


def _get_redis_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


def make_event(
    session_id: str,
    agent_id: str,
    agent_name: str,
    event_type: str,
    content: str | dict | list,
) -> AgentEvent:
    """Cria um evento padronizado para stream da sessão."""
    return AgentEvent(
        session_id=session_id,
        agent_id=agent_id,
        agent_name=agent_name,
        event_type=event_type,
        content=content,
        timestamp=datetime.utcnow(),
    )


async def publish_event(session_id: str, event: AgentEvent) -> None:
    """Publica evento em canal Redis session:{session_id}."""
    redis = _get_redis_client()
    try:
        channel = f"session:{session_id}"
        await redis.publish(channel, event.model_dump_json())
        log_structured(logger, "event_published", session_id=session_id, agent_id=event.agent_id)
    finally:
        await redis.close()


async def subscribe_events(session_id: str) -> AsyncGenerator[AgentEvent, None]:
    """Escuta eventos de uma sessão até receber done/error."""
    redis = _get_redis_client()
    pubsub = redis.pubsub()
    channel = f"session:{session_id}"
    try:
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = json.loads(message["data"])
            event = AgentEvent.model_validate(data)
            log_structured(logger, "event_received", session_id=session_id, agent_id=event.agent_id)
            yield event
            if event.event_type in {"done", "error"}:
                break
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        await redis.close()
