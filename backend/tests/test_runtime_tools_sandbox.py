from __future__ import annotations

from types import SimpleNamespace

from tools.sandbox_runner import SandboxResult
from tools.runtime_tools import resolve_tools


class _RunnerStub:
    def __init__(self) -> None:
        self.calls = 0

    def run_callable(self, func, *args, policy=None, **kwargs):
        self.calls += 1
        return SandboxResult(ok=True, output=func(*args, **kwargs))


def test_resolved_tools_execute_via_sandbox(monkeypatch) -> None:
    stub = _RunnerStub()
    monkeypatch.setattr("tools.runtime_tools.DEFAULT_SANDBOX_RUNNER", stub)

    node = SimpleNamespace(tools=["filesystem"])
    tools = resolve_tools(node)

    filesystem_read = next(tool for tool in tools if getattr(tool, "__name__", "") == "filesystem_read")
    result = filesystem_read("/does/not/exist")

    assert stub.calls == 1
    assert "error" in result.lower()
