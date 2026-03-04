"""Centralized gateway for all tool execution with policy, budget and approvals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from governance.approval_queue import ApprovalQueue, get_approval_queue
from monitoring.tracing import get_tracer
from core.retry_engine import get_default_retry_engine, RetryEngine
from tools.sandbox_runner import DEFAULT_SANDBOX_RUNNER, SandboxPolicy


@dataclass(slots=True)
class GatewayPolicy:
    require_approval_categories: set[str]
    blocked_tools: set[str]
    max_tool_cost: float = 10.0


class ExecutionGateway:
    def __init__(
        self,
        *,
        approval_queue: ApprovalQueue | None = None,
        policy: GatewayPolicy | None = None,
        retry_engine: RetryEngine | None = None,
    ) -> None:
        self.approval_queue = approval_queue or get_approval_queue()
        self.policy = policy or GatewayPolicy(require_approval_categories={"system", "integration"}, blocked_tools=set())
        self._spent_cost = 0.0
        self._tracer = get_tracer()
        self.retry_engine = retry_engine or get_default_retry_engine()

    def execute_tool(self, *, tool_name: str, category: str, handler: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any], estimated_cost: float = 0.0) -> Any:
        if tool_name in self.policy.blocked_tools:
            raise PermissionError(f"Tool blocked by policy: {tool_name}")
        if self._spent_cost + estimated_cost > self.policy.max_tool_cost:
            raise RuntimeError("Execution gateway budget exceeded")
        if category in self.policy.require_approval_categories:
            token = f"tool:{tool_name}:{self._spent_cost:.2f}"
            request = self.approval_queue.submit(token=token, reason=f"Tool approval required for {tool_name}", payload={"category": category})
            if request.status != "approved":
                raise PermissionError(f"Approval required before running tool {tool_name}")

        operation = "external_api" if category == "integration" or "api" in tool_name else "tool_call"
        with self._tracer.start_span(f"tool.{tool_name}", kind="tool_call", attributes={"tool": tool_name, "category": category}):
            def _run_sandbox() -> Any:
                sandbox_result = DEFAULT_SANDBOX_RUNNER.run_callable(handler, *args, policy=SandboxPolicy(), **kwargs)
                if not sandbox_result.ok:
                    raise RuntimeError(f"Sandbox execution failed: {sandbox_result.error}")
                return sandbox_result.output

            output = self.retry_engine.execute(
                operation,
                _run_sandbox,
                context={"tool_name": tool_name, "category": category},
            )
        self._spent_cost += max(estimated_cost, 0.0)
        return output
