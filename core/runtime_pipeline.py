"""Mandatory runtime pipeline for agent actions.

Execution flow:
agent_action -> execution_gateway -> policy_engine -> budget_manager -> sandbox_runner -> tool_invocation
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Callable

from monitoring.runtime_metrics import runtime_metrics

from governance.approval_queue import ApprovalQueue
from governance.policy_engine import PolicyEngine, PolicyViolationError
from tools.sandbox_runner import SandboxPolicy, SandboxRunner


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
    tenant_id: str = "default"


class BudgetManager:
    """Tracks cumulative execution spend for runtime actions."""

    def __init__(self, *, max_budget: float, tenant_budgets: dict[str, float] | None = None) -> None:
        self.max_budget = max_budget
        self._spent = 0.0
        self._tenant_spend: dict[str, float] = {}
        self.tenant_budgets = tenant_budgets or {}

    @property
    def spent(self) -> float:
        return self._spent

    def reserve(self, cost: float, *, tenant_id: str = "default") -> None:
        incremental = max(float(cost), 0.0)
        if self._spent + incremental > self.max_budget:
            raise BudgetExceededError(f"Execution budget exceeded: {self._spent + incremental:.2f} > {self.max_budget:.2f}")
        tenant_limit = self.tenant_budgets.get(tenant_id)
        tenant_spend = self._tenant_spend.get(tenant_id, 0.0)
        if tenant_limit is not None and tenant_spend + incremental > tenant_limit:
            raise BudgetExceededError(f"Tenant budget exceeded: {tenant_spend + incremental:.2f} > {tenant_limit:.2f}")
        self._spent += incremental
        self._tenant_spend[tenant_id] = tenant_spend + incremental


class RuntimePipeline:
    """Executes every agent action through policy, budget, approval, and sandbox controls."""

    def __init__(
        self,
        *,
        policy_engine: PolicyEngine,
        budget_manager: BudgetManager,
        sandbox_runner: SandboxRunner,
        approval_queue: ApprovalQueue,
        max_actions_per_tenant: int = 1000,
        max_actions_per_minute_per_tenant: int = 240,
        max_tool_invocations_per_tenant: dict[str, int] | None = None,
        max_consecutive_tool_invocations: int = 25,
        action_cooldown_seconds: float = 0.0,
    ) -> None:
        self.policy_engine = policy_engine
        self.budget_manager = budget_manager
        self.sandbox_runner = sandbox_runner
        self.approval_queue = approval_queue
        self.max_actions_per_tenant = max(1, max_actions_per_tenant)
        self.max_actions_per_minute_per_tenant = max(1, max_actions_per_minute_per_tenant)
        self.max_tool_invocations_per_tenant = max_tool_invocations_per_tenant or {}
        self.max_consecutive_tool_invocations = max(1, max_consecutive_tool_invocations)
        self.action_cooldown_seconds = max(0.0, action_cooldown_seconds)
        self._tenant_action_counts: dict[str, int] = {}
        self._last_action_at: dict[str, float] = {}
        self._tenant_tool_invocations: dict[str, dict[str, int]] = {}
        self._tenant_rate_windows: dict[str, tuple[float, int]] = {}
        self._tenant_last_tool: dict[str, str] = {}
        self._tenant_consecutive_tool_invocations: dict[str, int] = {}

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

    def _enforce_execution_guard(self, action: AgentAction) -> None:
        tenant = action.tenant_id or "default"
        actions = self._tenant_action_counts.get(tenant, 0)
        if actions >= self.max_actions_per_tenant:
            raise BudgetExceededError(f"Tenant action limit exceeded for {tenant}")
        now = time.monotonic()
        window_started_at, window_count = self._tenant_rate_windows.get(tenant, (now, 0))
        if now - window_started_at >= 60.0:
            window_started_at, window_count = now, 0
        if window_count >= self.max_actions_per_minute_per_tenant:
            raise RuntimeError(f"Tenant action rate limited for {tenant}")
        tool_counts = self._tenant_tool_invocations.setdefault(tenant, {})
        tool_count = tool_counts.get(action.tool_name, 0)
        per_tool_limit = self.max_tool_invocations_per_tenant.get(action.tool_name)
        if per_tool_limit is not None and tool_count >= per_tool_limit:
            raise RuntimeError(f"Tool invocation limit exceeded for {action.tool_name} under tenant {tenant}")
        previous_tool = self._tenant_last_tool.get(tenant)
        consecutive = self._tenant_consecutive_tool_invocations.get(tenant, 0)
        if previous_tool == action.tool_name and consecutive >= self.max_consecutive_tool_invocations:
            raise RuntimeError(f"Consecutive tool invocation limit exceeded for {action.tool_name} under tenant {tenant}")
        last = self._last_action_at.get(tenant)
        if last is not None and (now - last) < self.action_cooldown_seconds:
            raise RuntimeError(f"Action throttled for tenant {tenant}")
        self._tenant_rate_windows[tenant] = (window_started_at, window_count + 1)

    def execute(self, action: AgentAction) -> Any:
        self._validate_policy(action)
        self._enforce_approval(action)
        self._enforce_execution_guard(action)
        self.budget_manager.reserve(action.estimated_cost, tenant_id=action.tenant_id)
        runtime_metrics.inc("runtime_pipeline.actions")

        sandbox_result = self.sandbox_runner.run_callable(
            action.handler,
            *action.args,
            policy=action.sandbox_policy or SandboxPolicy(),
            **action.kwargs,
        )
        if not sandbox_result.ok:
            runtime_metrics.inc("runtime_pipeline.failures")
            raise RuntimeError(f"Sandbox execution failed: {sandbox_result.error}")
        tenant = action.tenant_id or "default"
        self._tenant_action_counts[tenant] = self._tenant_action_counts.get(tenant, 0) + 1
        tool_counts = self._tenant_tool_invocations.setdefault(tenant, {})
        tool_counts[action.tool_name] = tool_counts.get(action.tool_name, 0) + 1
        if self._tenant_last_tool.get(tenant) == action.tool_name:
            self._tenant_consecutive_tool_invocations[tenant] = self._tenant_consecutive_tool_invocations.get(tenant, 0) + 1
        else:
            self._tenant_last_tool[tenant] = action.tool_name
            self._tenant_consecutive_tool_invocations[tenant] = 1
        self._last_action_at[tenant] = time.monotonic()
        runtime_metrics.inc("runtime_pipeline.success")
        return sandbox_result.output
