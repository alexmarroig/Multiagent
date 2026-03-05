"""Token budget scheduler for per-agent, per-tenant, and global budget governance."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from monitoring.runtime_metrics import runtime_metrics


@dataclass(slots=True)
class TokenBudgetConfig:
    global_budget: int = 20_000_000
    default_agent_budget: int = 100_000
    default_tenant_budget: int = 2_000_000
    hard_limit_factor: float = 1.2


class TokenBudgetScheduler:
    """Tracks token usage and decides whether agents should run, pause, or delay."""

    def __init__(self, config: TokenBudgetConfig | None = None) -> None:
        self.config = config or TokenBudgetConfig()
        self._global_used = 0
        self._agent_used: dict[str, int] = defaultdict(int)
        self._tenant_used: dict[str, int] = defaultdict(int)
        self._tenant_reserved: dict[str, int] = defaultdict(int)

    def record_usage(self, *, agent_id: str, tenant_id: str, tokens: int) -> None:
        consumed = max(0, int(tokens))
        self._global_used += consumed
        self._agent_used[agent_id] += consumed
        self._tenant_used[tenant_id] += consumed
        self._tenant_reserved[tenant_id] = max(0, self._tenant_reserved[tenant_id] - consumed)
        runtime_metrics.inc("token.consumed", float(consumed))
        runtime_metrics.set_gauge("token.global_used", float(self._global_used))


    def reserve(self, *, tenant_id: str, tokens: int) -> bool:
        planned = max(0, int(tokens))
        hard_limit = int(self.config.default_tenant_budget * self.config.hard_limit_factor)
        if self._tenant_used[tenant_id] + self._tenant_reserved[tenant_id] + planned > hard_limit:
            runtime_metrics.inc("token.reserve_rejected")
            return False
        self._tenant_reserved[tenant_id] += planned
        runtime_metrics.set_gauge(f"token.tenant_reserved.{tenant_id}", float(self._tenant_reserved[tenant_id]))
        return True

    def should_throttle(self, *, agent_id: str, tenant_id: str, critical: bool = False) -> tuple[bool, str | None]:
        if self._global_used >= self.config.global_budget:
            return (not critical), "global_budget"
        if self._tenant_used[tenant_id] >= self.config.default_tenant_budget:
            return True, "tenant_budget"
        if self._agent_used[agent_id] >= self.config.default_agent_budget:
            return True, "agent_budget"
        return False, None

    def action_for_agent(self, *, agent_id: str, tenant_id: str, critical: bool = False) -> str:
        throttle, reason = self.should_throttle(agent_id=agent_id, tenant_id=tenant_id, critical=critical)
        if not throttle:
            return "run"
        if reason == "global_budget" and not critical:
            return "pause_non_critical"
        return "delay"

    def snapshot(self) -> dict[str, int]:
        return {
            "global_used": self._global_used,
            "agent_count": len(self._agent_used),
            "tenant_count": len(self._tenant_used),
            "reserved_tokens": sum(self._tenant_reserved.values()),
        }
