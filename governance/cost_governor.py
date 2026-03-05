"""Cost governance for LLM, tools, and compute usage across tenants and executions."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(slots=True)
class CostLimits:
    per_user: float = 25.0
    per_tenant: float = 500.0
    per_execution: float = 10.0


class CostGovernor:
    def __init__(self, limits: CostLimits | None = None) -> None:
        self.limits = limits or CostLimits()
        self._user_costs: dict[str, float] = defaultdict(float)
        self._tenant_costs: dict[str, float] = defaultdict(float)
        self._execution_costs: dict[str, float] = defaultdict(float)

    def track(self, *, user_id: str, tenant_id: str, execution_id: str, llm_cost: float = 0.0, tool_cost: float = 0.0, compute_cost: float = 0.0) -> float:
        total = max(0.0, llm_cost) + max(0.0, tool_cost) + max(0.0, compute_cost)
        self._user_costs[user_id] += total
        self._tenant_costs[tenant_id] += total
        self._execution_costs[execution_id] += total
        return total

    def is_allowed(self, *, user_id: str, tenant_id: str, execution_id: str) -> tuple[bool, str | None]:
        if self._execution_costs[execution_id] > self.limits.per_execution:
            return False, "per_execution"
        if self._user_costs[user_id] > self.limits.per_user:
            return False, "per_user"
        if self._tenant_costs[tenant_id] > self.limits.per_tenant:
            return False, "per_tenant"
        return True, None

    def snapshot(self) -> dict[str, int]:
        return {
            "users": len(self._user_costs),
            "tenants": len(self._tenant_costs),
            "executions": len(self._execution_costs),
        }
