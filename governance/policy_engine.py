"""Policy enforcement for autonomous agent workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Policy:
    require_human_approval: bool = False
    max_cost: float | None = None
    max_risk_level: str | None = None
    restricted_tools: set[str] = field(default_factory=set)


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    reason: str
    violations: list[str]
    requires_human_approval: bool


class PolicyViolationError(RuntimeError):
    """Raised when a task violates configured governance policies."""


class PolicyEngine:
    _RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def __init__(self, policy: Policy | None = None) -> None:
        self.policy = policy or Policy()

    def _risk_value(self, risk: str | None) -> int:
        return self._RISK_ORDER.get((risk or "low").lower(), 1)

    def evaluate_violations(self, task: dict[str, Any]) -> list[str]:
        violations: list[str] = []
        tool = str(task.get("tool", task.get("tool_id", "")))
        if tool and tool in self.policy.restricted_tools:
            violations.append(f"tool_restricted:{tool}")

        if self.policy.max_cost is not None and float(task.get("estimated_cost", 0.0)) > self.policy.max_cost:
            violations.append("cost_limit_exceeded")

        if self.policy.max_risk_level is not None:
            if self._risk_value(task.get("risk_level")) > self._risk_value(self.policy.max_risk_level):
                violations.append("risk_limit_exceeded")

        return violations

    def evaluate(self, task: dict[str, Any], actor: str | None = None) -> PolicyDecision:
        violations = self.evaluate_violations(task)
        requires_human_approval = self.policy.require_human_approval and not bool(task.get("human_approved", False))
        if requires_human_approval:
            violations.append("human_approval_required")

        allowed = len([v for v in violations if v != "human_approval_required"]) == 0
        reason = "ok" if not violations else ", ".join(violations)
        return PolicyDecision(
            allowed=allowed,
            reason=reason,
            violations=violations,
            requires_human_approval=requires_human_approval,
        )

    def enforce(self, task: dict[str, Any]) -> None:
        decision = self.evaluate(task)
        if not decision.allowed:
            raise PolicyViolationError(f"Policy violation(s): {decision.reason}")
