"""Central runtime for autonomous agent lifecycle management."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class RuntimeStatus(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPED = "stopped"


class RuntimeLoop(Protocol):
    """Contract for an autonomy loop executed by the runtime."""

    def run_cycle(self) -> dict:
        ...


@dataclass(slots=True)
class AgentProfile:
    agent_id: str
    skills: set[str] = field(default_factory=set)
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class RuntimeHealth:
    status: RuntimeStatus
    active_agents: int
    loop_iterations: int
    spent_cost: float
    uptime_seconds: float
    last_error: str | None = None


class AgentRuntime:
    """Maintains agent lifecycle, loop execution, budgets, and health telemetry."""

    def __init__(self, *, max_runtime_cost: float = 25.0, logger: logging.Logger | None = None) -> None:
        self.max_runtime_cost = max_runtime_cost
        self.logger = logger or logging.getLogger(__name__)
        self.status = RuntimeStatus.INITIALIZING
        self._started_at = time.monotonic()
        self._agents: dict[str, AgentProfile] = {}
        self._iterations = 0
        self._spent_cost = 0.0
        self._last_error: str | None = None

    def initialize_agents(self, agents: list[AgentProfile]) -> None:
        self._agents = {agent.agent_id: agent for agent in agents}
        self.status = RuntimeStatus.RUNNING

    def create_specialized_agent(self, skill: str) -> AgentProfile:
        """Spawn a new specialized agent when no existing agent has the required skill."""
        agent_id = f"agent-{len(self._agents) + 1:03d}"
        profile = AgentProfile(agent_id=agent_id, skills={skill}, metadata={"spawned": True})
        self._agents[agent_id] = profile
        self.logger.info("Spawned specialized agent %s for skill %s", agent_id, skill)
        return profile

    def resolve_agent_for_skill(self, skill: str) -> AgentProfile:
        for agent in self._agents.values():
            if skill in agent.skills:
                return agent
        return self.create_specialized_agent(skill)

    def enforce_cost_limit(self, incremental_cost: float) -> bool:
        self._spent_cost += max(incremental_cost, 0.0)
        if self._spent_cost > self.max_runtime_cost:
            self.status = RuntimeStatus.DEGRADED
            self.logger.warning("Runtime budget exceeded: %.2f > %.2f", self._spent_cost, self.max_runtime_cost)
            return False
        return True

    def monitor_health(self) -> RuntimeHealth:
        return RuntimeHealth(
            status=self.status,
            active_agents=len(self._agents),
            loop_iterations=self._iterations,
            spent_cost=round(self._spent_cost, 4),
            uptime_seconds=round(time.monotonic() - self._started_at, 2),
            last_error=self._last_error,
        )

    def execution_loop(self, autonomy_loop: RuntimeLoop, *, max_cycles: int = 50) -> RuntimeHealth:
        self.status = RuntimeStatus.RUNNING

        while self.status == RuntimeStatus.RUNNING and self._iterations < max_cycles:
            try:
                cycle_result = autonomy_loop.run_cycle()
                self._iterations += 1
                if not self.enforce_cost_limit(float(cycle_result.get("cost", 0.0))):
                    break
                if cycle_result.get("halt"):
                    break
            except Exception as exc:  # noqa: BLE001
                self.status = RuntimeStatus.DEGRADED
                self._last_error = str(exc)
                self.logger.exception("Runtime loop failed")
                break

        self.status = RuntimeStatus.STOPPED if self.status != RuntimeStatus.DEGRADED else RuntimeStatus.DEGRADED
        return self.monitor_health()
