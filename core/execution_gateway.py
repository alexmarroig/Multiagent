"""Centralized gateway for all agent actions via the mandatory runtime pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from governance.approval_queue import ApprovalQueue, get_approval_queue
from governance.policy_engine import Policy, PolicyEngine
from monitoring.tracing import get_tracer
from tools.sandbox_runner import DEFAULT_SANDBOX_RUNNER, SandboxPolicy, SandboxRunner

from core.runtime_pipeline import AgentAction, BudgetManager, RuntimePipeline


@dataclass(slots=True)
class GatewayPolicy:
    require_approval_categories: set[str]
    blocked_tools: set[str]
    max_tool_cost: float = 10.0
    max_risk_level: str | None = None


class ExecutionGateway:
    def __init__(
        self,
        *,
        approval_queue: ApprovalQueue | None = None,
        policy: GatewayPolicy | None = None,
        sandbox_runner: SandboxRunner | None = None,
    ) -> None:
        self.approval_queue = approval_queue or get_approval_queue()
        self.policy = policy or GatewayPolicy(require_approval_categories={"system", "integration"}, blocked_tools=set())
        self._tracer = get_tracer()
        self._pipeline = RuntimePipeline(
            policy_engine=PolicyEngine(
                Policy(
                    require_human_approval=False,
                    max_cost=self.policy.max_tool_cost,
                    max_risk_level=self.policy.max_risk_level,
                    restricted_tools=set(self.policy.blocked_tools),
                )
            ),
            budget_manager=BudgetManager(max_budget=self.policy.max_tool_cost),
            sandbox_runner=sandbox_runner or DEFAULT_SANDBOX_RUNNER,
            approval_queue=self.approval_queue,
        )

    def execute_tool(
        self,
        *,
        tool_name: str,
        category: str,
        handler: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        estimated_cost: float = 0.0,
        risk_level: str = "low",
        sandbox_policy: SandboxPolicy | None = None,
    ) -> Any:
        return self.execute_agent_action(
            tool_name=tool_name,
            category=category,
            handler=handler,
            args=args,
            kwargs=kwargs,
            estimated_cost=estimated_cost,
            risk_level=risk_level,
            sandbox_policy=sandbox_policy,
        )

    def execute_agent_action(
        self,
        *,
        tool_name: str,
        category: str,
        handler: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        estimated_cost: float = 0.0,
        risk_level: str = "low",
        sandbox_policy: SandboxPolicy | None = None,
    ) -> Any:
        with self._tracer.start_span(
            f"agent_action.{tool_name}",
            kind="tool_call",
            attributes={"tool": tool_name, "category": category},
        ):
            return self._pipeline.execute(
                AgentAction(
                    tool_name=tool_name,
                    category=category,
                    handler=handler,
                    args=args,
                    kwargs=kwargs,
                    estimated_cost=estimated_cost,
                    risk_level=risk_level,
                    require_approval=category in self.policy.require_approval_categories,
                    sandbox_policy=sandbox_policy or SandboxPolicy(),
                )
            )
