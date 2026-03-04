"""Telemetry aggregation service for traces, logs, and metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class TelemetryEvent:
    name: str
    payload: dict[str, Any]
    timestamp: str


class TelemetryService:
    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    def record(self, name: str, payload: dict[str, Any]) -> None:
        self._events.append(TelemetryEvent(name=name, payload=payload, timestamp=datetime.now(timezone.utc).isoformat()))

    def list_events(self) -> list[TelemetryEvent]:
        return list(self._events)
