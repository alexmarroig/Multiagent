"""Controls agent spawning using global, per-goal, rate, and depth limits."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class SpawnLimits:
    max_agents_global: int = 10_000
    max_agents_per_goal: int = 250
    max_spawn_per_minute: int = 1_000
    max_recursion_depth: int = 6


@dataclass(slots=True)
class SpawnRequest:
    goal_id: str
    parent_agent_id: str
    agent_type: str
    recursion_depth: int = 0
    metadata: dict = field(default_factory=dict)


class SpawnController:
    """Prevents uncontrolled fan-out while preserving throughput via queueing."""

    def __init__(self, limits: SpawnLimits | None = None) -> None:
        self.limits = limits or SpawnLimits()
        self._active_agents_global = 0
        self._active_agents_per_goal: dict[str, int] = defaultdict(int)
        self._spawn_timestamps: deque[float] = deque()
        self._deferred_requests: deque[SpawnRequest] = deque()

    def can_spawn(self, request: SpawnRequest) -> tuple[bool, str | None]:
        self._prune_old_timestamps()
        if request.recursion_depth > self.limits.max_recursion_depth:
            return False, "max_recursion_depth"
        if self._active_agents_global >= self.limits.max_agents_global:
            return False, "max_agents_global"
        if self._active_agents_per_goal[request.goal_id] >= self.limits.max_agents_per_goal:
            return False, "max_agents_per_goal"
        if len(self._spawn_timestamps) >= self.limits.max_spawn_per_minute:
            return False, "max_spawn_per_minute"
        return True, None

    def request_spawn(self, request: SpawnRequest) -> bool:
        allowed, _reason = self.can_spawn(request)
        if not allowed:
            self._deferred_requests.append(request)
            return False
        self._spawn_timestamps.append(time.time())
        self._active_agents_global += 1
        self._active_agents_per_goal[request.goal_id] += 1
        return True

    def complete_agent(self, goal_id: str) -> None:
        self._active_agents_global = max(0, self._active_agents_global - 1)
        self._active_agents_per_goal[goal_id] = max(0, self._active_agents_per_goal[goal_id] - 1)

    def pop_deferred_request(self) -> SpawnRequest | None:
        if not self._deferred_requests:
            return None
        request = self._deferred_requests.popleft()
        if self.request_spawn(request):
            return request
        self._deferred_requests.appendleft(request)
        return None

    def metrics(self) -> dict[str, int]:
        self._prune_old_timestamps()
        return {
            "active_agents_global": self._active_agents_global,
            "spawned_last_minute": len(self._spawn_timestamps),
            "deferred_requests": len(self._deferred_requests),
        }

    def _prune_old_timestamps(self) -> None:
        cutoff = time.time() - 60
        while self._spawn_timestamps and self._spawn_timestamps[0] < cutoff:
            self._spawn_timestamps.popleft()
