"""Episodic memory for short-to-mid horizon execution traces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Episode:
    episode_id: str
    summary: str
    context: dict[str, Any]
    recorded_at: str


class EpisodicMemory:
    def __init__(self) -> None:
        self._episodes: list[Episode] = []

    def append(self, *, episode_id: str, summary: str, context: dict[str, Any]) -> Episode:
        episode = Episode(
            episode_id=episode_id,
            summary=summary,
            context=context,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
        self._episodes.append(episode)
        return episode

    def latest(self, limit: int = 10) -> list[Episode]:
        return self._episodes[-max(limit, 1) :]
