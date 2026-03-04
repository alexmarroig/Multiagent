from __future__ import annotations

import pytest

from core.execution_gateway import ExecutionGateway, GatewayPolicy
from governance.approval_queue import ApprovalQueue
from governance.policy_engine import PolicyViolationError
from tools.sandbox_runner import SandboxResult


class _RunnerStub:
    def run_callable(self, func, *args, policy=None, **kwargs):
        return SandboxResult(ok=True, output=func(*args, **kwargs))


def test_execution_gateway_enforces_policy_and_budget() -> None:
    gateway = ExecutionGateway(
        policy=GatewayPolicy(require_approval_categories=set(), blocked_tools={"blocked"}, max_tool_cost=1.0),
        sandbox_runner=_RunnerStub(),
    )

    with pytest.raises(PolicyViolationError):
        gateway.execute_agent_action(
            tool_name="blocked",
            category="tool",
            handler=lambda: "nope",
            args=(),
            kwargs={},
        )

    gateway.execute_agent_action(
        tool_name="ok",
        category="tool",
        handler=lambda: "ok",
        args=(),
        kwargs={},
        estimated_cost=0.7,
    )

    with pytest.raises(RuntimeError, match="budget exceeded"):
        gateway.execute_agent_action(
            tool_name="ok2",
            category="tool",
            handler=lambda: "ok",
            args=(),
            kwargs={},
            estimated_cost=0.4,
        )


def test_execution_gateway_enforces_approval_workflow() -> None:
    queue = ApprovalQueue()
    gateway = ExecutionGateway(
        approval_queue=queue,
        policy=GatewayPolicy(require_approval_categories={"integration"}, blocked_tools=set(), max_tool_cost=10),
        sandbox_runner=_RunnerStub(),
    )

    with pytest.raises(PermissionError, match="Approval required"):
        gateway.execute_agent_action(
            tool_name="api_call",
            category="integration",
            handler=lambda: "ok",
            args=(),
            kwargs={},
        )
