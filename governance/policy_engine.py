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


class PolicyViolationError(RuntimeError):
    """Raised when a task violates configured governance policies."""


class PolicyEngine:
    _RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    def __init__(self, policy: Policy | None = None) -> None:
        self.policy = policy or Policy()

    def _risk_value(self, risk: str | None) -> int:
        return self._RISK_ORDER.get((risk or "low").lower(), 1)

    def evaluate(self, task: dict[str, Any]) -> list[str]:
        violations: list[str] = []
        tool = str(task.get("tool", task.get("tool_id", "")))
        if tool and tool in self.policy.restricted_tools:
            violations.append(f"tool_restricted:{tool}")

        if self.policy.max_cost is not None and float(task.get("estimated_cost", 0.0)) > self.policy.max_cost:
            violations.append("cost_limit_exceeded")

        if self.policy.max_risk_level is not None:
            if self._risk_value(task.get("risk_level")) > self._risk_value(self.policy.max_risk_level):
                violations.append("risk_limit_exceeded")

        if self.policy.require_human_approval and not bool(task.get("human_approved", False)):
            violations.append("human_approval_required")

        return violations

    def enforce(self, task: dict[str, Any]) -> None:
        violations = self.evaluate(task)
        if violations:
            raise PolicyViolationError(f"Policy violation(s): {', '.join(violations)}")
