"""Rate and token governor for safe and affordable LLM usage."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(slots=True)
class LLMGovernorLimits:
    max_requests_per_minute_per_agent: int = 120
    max_tokens_per_task: int = 12_000
    max_tokens_per_tenant_per_hour: int = 1_000_000


class LLMRequestGovernor:
    """Applies per-agent and tenant-level request/token safety budgets."""

    def __init__(self, limits: LLMGovernorLimits | None = None) -> None:
        self.limits = limits or LLMGovernorLimits()
        self._agent_request_timestamps: dict[str, deque[float]] = defaultdict(deque)
        self._tenant_token_usage: dict[str, deque[tuple[float, int]]] = defaultdict(deque)

    def check_request(self, *, agent_id: str, tenant_id: str, task_id: str, tokens_requested: int) -> tuple[bool, str]:
        """Return allow/delay/reject decisions based on configured limits."""

        del task_id  # task_id included for audit extension points.
        self._prune()

        if tokens_requested > self.limits.max_tokens_per_task:
            return False, "reject:max_tokens_per_task"

        agent_window = self._agent_request_timestamps[agent_id]
        if len(agent_window) >= self.limits.max_requests_per_minute_per_agent:
            return False, "delay:max_requests_per_minute_per_agent"

        tenant_total = sum(tokens for _, tokens in self._tenant_token_usage[tenant_id])
        if tenant_total + tokens_requested > self.limits.max_tokens_per_tenant_per_hour:
            return False, "reject:max_tokens_per_tenant_per_hour"

        now = time.time()
        agent_window.append(now)
        self._tenant_token_usage[tenant_id].append((now, tokens_requested))
        return True, "allow"

    def metrics(self) -> dict[str, float]:
        self._prune()
        token_rate = sum(tokens for records in self._tenant_token_usage.values() for _, tokens in records) / 3600.0
        return {"token_consumption_rate": float(token_rate)}

    def _prune(self) -> None:
        now = time.time()
        request_cutoff = now - 60
        token_cutoff = now - 3600

        for timestamps in self._agent_request_timestamps.values():
            while timestamps and timestamps[0] < request_cutoff:
                timestamps.popleft()

        for records in self._tenant_token_usage.values():
            while records and records[0][0] < token_cutoff:
                records.popleft()
