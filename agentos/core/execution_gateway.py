"""Centralized gateway for all agent actions via the mandatory runtime pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Tuple, Dict

from agentos.governance.approval_queue import ApprovalQueue, get_approval_queue
from agentos.governance.policy_engine import Policy, PolicyEngine
from agentos.monitoring.tracing import get_tracer

from agentos.tools.sandbox_runner import (
    DEFAULT_SANDBOX_RUNNER,
    SandboxPolicy,
    SandboxRunner,
)

from agentos.core.runtime_pipeline import (
    AgentAction,
    BudgetManager,
    RuntimePipeline,
)

from agentos.core.retry_engine import (
    RetryEngine,
    get_default_retry_engine,
)


@dataclass(slots=True)
class GatewayPolicy:
    """Configuration for gateway governance."""

    require_approval_categories: set[str]
    blocked_tools: set[str]
    max_tool_cost: float = 10.0
    max_risk_level: str | None = None


class ExecutionGateway:
    """
    Central execution gateway.

    ALL agent actions must pass through this gateway to enforce:
    - policy governance
    - human approval
    - sandboxing
    - cost control
    - tracing
    """

    def __init__(
        self,
        *,
        approval_queue: ApprovalQueue | None = None,
        policy: GatewayPolicy | None = None,
        sandbox_runner: SandboxRunner | None = None,
        retry_engine: RetryEngine | None = None,
    ) -> None:

        self.approval_queue = approval_queue or get_approval_queue()

        self.policy = policy or GatewayPolicy(
            require_approval_categories={"system", "integration"},
            blocked_tools=set(),
        )

        self.retry_engine = retry_engine or get_default_retry_engine()

        self._tracer = get_tracer()

        self._spent_cost: float = 0.0

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
        args: Tuple[Any, ...] = (),
        kwargs: Dict[str, Any] | None = None,
        estimated_cost: float = 0.0,
        risk_level: str = "low",
        sandbox_policy: SandboxPolicy | None = None,
    ) -> Any:
        """
        Public entrypoint for executing a tool.
        """

        kwargs = kwargs or {}

        if tool_name in self.policy.blocked_tools:
            raise PermissionError(f"Tool blocked by policy: {tool_name}")

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
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        estimated_cost: float = 0.0,
        risk_level: str = "low",
        sandbox_policy: SandboxPolicy | None = None,
    ) -> Any:
        """
        Execute an agent action through the runtime pipeline.
        """

        with self._tracer.start_span(
            f"agent_action.{tool_name}",
            kind="tool_call",
            attributes={
                "tool": tool_name,
                "category": category,
                "risk_level": risk_level,
            },
        ):

            result = self._pipeline.execute(
                AgentAction(
                    tool_name=tool_name,
                    category=category,
                    handler=handler,
                    args=args,
                    kwargs=kwargs,
                    estimated_cost=estimated_cost,
                    risk_level=risk_level,
                    require_approval=(
                        category in self.policy.require_approval_categories
                    ),
                    sandbox_policy=sandbox_policy or SandboxPolicy(),
                )
            )

            self._spent_cost += max(estimated_cost, 0.0)

            return result