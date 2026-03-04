"""Guardrails and cost controls for safe production autonomy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GuardrailDecision:
    allowed: bool
    reason: str


class Guardrails:
    def __init__(self, hard_cost_ceiling: float = 100.0) -> None:
        self.hard_cost_ceiling = hard_cost_ceiling

    def evaluate_cost(self, run_report: dict[str, Any], budget_limit_usd: float) -> GuardrailDecision:
        cost = float(run_report.get("cost", 0.0))
        limit = min(self.hard_cost_ceiling, budget_limit_usd)
        if cost > limit:
            return GuardrailDecision(allowed=False, reason="cost_limit_exceeded")
        return GuardrailDecision(allowed=True, reason="ok")

    def enforce(self, run_report: dict[str, Any], budget_limit_usd: float) -> dict[str, Any]:
        decision = self.evaluate_cost(run_report, budget_limit_usd)
        return {**run_report, "guardrails": {"allowed": decision.allowed, "reason": decision.reason}}
