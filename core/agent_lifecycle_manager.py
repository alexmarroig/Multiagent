"""Agent lifecycle state machine with idle termination."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class AgentState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass(slots=True)
class LifecycleRecord:
    agent_id: str
    state: AgentState = AgentState.CREATED
    updated_at: float = field(default_factory=time.time)
    reason: str | None = None


class AgentLifecycleManager:
    def __init__(self, *, idle_timeout_seconds: int = 300) -> None:
        self.idle_timeout_seconds = max(1, idle_timeout_seconds)
        self._records: dict[str, LifecycleRecord] = {}

    def register(self, agent_id: str) -> LifecycleRecord:
        record = LifecycleRecord(agent_id=agent_id)
        self._records[agent_id] = record
        return record

    def transition(self, agent_id: str, state: AgentState, reason: str | None = None) -> LifecycleRecord:
        record = self._records.setdefault(agent_id, LifecycleRecord(agent_id=agent_id))
        record.state = state
        record.reason = reason
        record.updated_at = time.time()
        return record

    def terminate_idle_agents(self) -> list[str]:
        now = time.time()
        terminated: list[str] = []
        for agent_id, record in self._records.items():
            idle = now - record.updated_at
            if record.state in {AgentState.RUNNING, AgentState.WAITING} and idle > self.idle_timeout_seconds:
                record.state = AgentState.TERMINATED
                record.reason = "idle_timeout"
                record.updated_at = now
                terminated.append(agent_id)
        return terminated

    def get(self, agent_id: str) -> LifecycleRecord | None:
        return self._records.get(agent_id)
