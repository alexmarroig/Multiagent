"""Persistent pool management for reusable specialized agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass(slots=True)
class PooledAgent:
    agent_id: str
    specializations: set[str] = field(default_factory=set)
    capacity: int = 1
    current_load: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def available(self) -> bool:
        return self.current_load < self.capacity


class AgentPool:
    """Manages reusable agents, specialization routing, and resource-aware allocation."""

    def __init__(self) -> None:
        self._agents: dict[str, PooledAgent] = {}
        self._lock = Lock()

    def register_agent(self, agent: PooledAgent) -> None:
        with self._lock:
            self._agents[agent.agent_id] = agent

    def acquire_agent(self, specialization: str | None = None) -> PooledAgent | None:
        with self._lock:
            candidates = [agent for agent in self._agents.values() if agent.available]
            if specialization:
                candidates = [agent for agent in candidates if specialization in agent.specializations]
            if not candidates:
                return None
            selected = min(candidates, key=lambda agent: agent.current_load)
            selected.current_load += 1
            return selected

    def release_agent(self, agent_id: str) -> None:
        with self._lock:
            if agent_id in self._agents and self._agents[agent_id].current_load > 0:
                self._agents[agent_id].current_load -= 1

    def auto_scale(self, specialization: str, count: int = 1, base_capacity: int = 2) -> list[PooledAgent]:
        created: list[PooledAgent] = []
        with self._lock:
            start = len(self._agents) + 1
            for idx in range(count):
                agent = PooledAgent(
                    agent_id=f"pool-agent-{start + idx:04d}",
                    specializations={specialization},
                    capacity=max(1, base_capacity),
                    metadata={"auto_scaled": True},
                )
                self._agents[agent.agent_id] = agent
                created.append(agent)
        return created

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "agents": len(self._agents),
                "load": {
                    agent_id: {
                        "specializations": sorted(agent.specializations),
                        "current_load": agent.current_load,
                        "capacity": agent.capacity,
                    }
                    for agent_id, agent in self._agents.items()
                },
            }
