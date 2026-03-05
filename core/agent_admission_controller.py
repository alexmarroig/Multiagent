"""Admission control for safe and fair agent startup at scale."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(slots=True)
class AdmissionLimits:
    """Limits used to protect the scheduler from startup storms."""

    max_concurrent_agents: int = 10_000
    max_spawn_rate_per_tenant_per_minute: int = 300
    max_global_spawn_burst_per_10s: int = 1_500


@dataclass(slots=True)
class AgentStartRequest:
    """Represents a request to start an agent process."""

    agent_id: str
    tenant_id: str
    requested_at: float = 0.0


class AgentAdmissionController:
    """Gates new agent starts through global and tenant-aware guardrails."""

    def __init__(self, limits: AdmissionLimits | None = None) -> None:
        self.limits = limits or AdmissionLimits()
        self._active_agents = 0
        self._active_by_tenant: dict[str, int] = defaultdict(int)
        self._tenant_spawn_timestamps: dict[str, deque[float]] = defaultdict(deque)
        self._global_spawn_timestamps: deque[float] = deque()
        self._start_queue: deque[AgentStartRequest] = deque()

    def request_start(self, request: AgentStartRequest) -> bool:
        """Accept immediately when safe, otherwise queue the request."""

        request.requested_at = request.requested_at or time.time()
        self._prune_windows()

        if not self._can_admit(request.tenant_id):
            self._start_queue.append(request)
            return False

        self._admit(request)
        return True

    def complete_agent(self, tenant_id: str) -> None:
        """Mark a running agent as complete and release capacity."""

        self._active_agents = max(0, self._active_agents - 1)
        self._active_by_tenant[tenant_id] = max(0, self._active_by_tenant[tenant_id] - 1)

    def pop_next_queued(self) -> AgentStartRequest | None:
        """Pop and admit one queued request if capacity is available."""

        if not self._start_queue:
            return None

        self._prune_windows()
        for _ in range(len(self._start_queue)):
            request = self._start_queue.popleft()
            if self._can_admit(request.tenant_id):
                self._admit(request)
                return request
            self._start_queue.append(request)
        return None

    def metrics(self) -> dict[str, float]:
        """Return safety metrics used by the platform controller."""

        self._prune_windows()
        return {
            "active_agents": float(self._active_agents),
            "queued_agent_starts": float(len(self._start_queue)),
            "agent_spawn_rate": float(len(self._global_spawn_timestamps) / 10.0),
        }

    def _can_admit(self, tenant_id: str) -> bool:
        if self._active_agents >= self.limits.max_concurrent_agents:
            return False
        if len(self._tenant_spawn_timestamps[tenant_id]) >= self.limits.max_spawn_rate_per_tenant_per_minute:
            return False
        if len(self._global_spawn_timestamps) >= self.limits.max_global_spawn_burst_per_10s:
            return False
        return True

    def _admit(self, request: AgentStartRequest) -> None:
        now = time.time()
        self._active_agents += 1
        self._active_by_tenant[request.tenant_id] += 1
        self._tenant_spawn_timestamps[request.tenant_id].append(now)
        self._global_spawn_timestamps.append(now)

    def _prune_windows(self) -> None:
        now = time.time()
        tenant_cutoff = now - 60
        burst_cutoff = now - 10

        for timestamps in self._tenant_spawn_timestamps.values():
            while timestamps and timestamps[0] < tenant_cutoff:
                timestamps.popleft()

        while self._global_spawn_timestamps and self._global_spawn_timestamps[0] < burst_cutoff:
            self._global_spawn_timestamps.popleft()
