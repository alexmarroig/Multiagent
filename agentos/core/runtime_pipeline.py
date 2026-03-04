"""Mandatory runtime pipeline for agent actions.

Execution flow:
agent_action -> execution_gateway -> policy_engine -> budget_manager -> sandbox_runner -> tool_invocation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from agentos.governance.approval_queue import ApprovalQueue
from agentos.governance.policy_engine import PolicyEngine, PolicyViolationError
from agentos.tools.sandbox_runner import SandboxPolicy, SandboxRunner


class BudgetExceededError(RuntimeError):
    """Raised when action execution exceeds the configured runtime budget."""


@dataclass(slots=True)
class AgentAction:
    tool_name: str
    category: str
    handler: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    estimated_cost: float = 0.0
    risk_level: str = "low"
    require_approval: bool = False
    sandbox_policy: SandboxPolicy | None = None


class BudgetManager:
    """Tracks cumulative execution spend for runtime actions."""

    def __init__(self, *, max_budget: float) -> None:
        self.max_budget = max_budget
        self._spent = 0.0

    @property
    def spent(self) -> float:
        return self._spent

    def reserve(self, cost: float) -> None:
        incremental = max(float(cost), 0.0)
        if self._spent + incremental > self.max_budget:
            raise BudgetExceededError(f"Execution budget exceeded: {self._spent + incremental:.2f} > {self.max_budget:.2f}")
        self._spent += incremental


class RuntimePipeline:
    """Executes every agent action through policy, budget, approval, and sandbox controls."""

    def __init__(
        self,
        *,
        policy_engine: PolicyEngine,
        budget_manager: BudgetManager,
        sandbox_runner: SandboxRunner,
        approval_queue: ApprovalQueue,
    ) -> None:
        self.policy_engine = policy_engine
        self.budget_manager = budget_manager
        self.sandbox_runner = sandbox_runner
        self.approval_queue = approval_queue

    def _validate_policy(self, action: AgentAction) -> None:
        decision = self.policy_engine.evaluate(
            {
                "tool": action.tool_name,
                "estimated_cost": action.estimated_cost,
                "risk_level": action.risk_level,
                "human_approved": False,
            }
        )
        blocking_violations = [item for item in decision.violations if item != "human_approval_required"]
        if blocking_violations:
            raise PolicyViolationError(f"Policy violation(s): {', '.join(blocking_violations)}")

    def _enforce_approval(self, action: AgentAction) -> None:
        if not action.require_approval and not self.policy_engine.policy.require_human_approval:
            return
        token = f"action:{action.tool_name}:{self.budget_manager.spent:.2f}"
        request = self.approval_queue.submit(
            token=token,
            reason=f"approval required for {action.tool_name}",
            payload={"tool": action.tool_name, "category": action.category},
        )
        if request.status != "approved":
            raise PermissionError(f"Approval required before running {action.tool_name}")

    def execute(self, action: AgentAction) -> Any:
        self._validate_policy(action)
        self._enforce_approval(action)
        self.budget_manager.reserve(action.estimated_cost)

        sandbox_result = self.sandbox_runner.run_callable(
            action.handler,
            *action.args,
            policy=action.sandbox_policy or SandboxPolicy(),
            **action.kwargs,
        )
        if not sandbox_result.ok:
            raise RuntimeError(f"Sandbox execution failed: {sandbox_result.error}")
        return sandbox_result.output

