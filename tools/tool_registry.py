"""Central tool registry and dynamic tool attachment for agents."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

from tools.sandbox_runner import DEFAULT_SANDBOX_RUNNER, SandboxPolicy


ToolCallable = Callable[..., Any]


@dataclass(slots=True)
class ToolSpec:
    name: str
    category: str
    handler: ToolCallable
    description: str = ""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools[tool.name] = tool

    def register_defaults(self) -> None:
        self.register(ToolSpec("web_search", "search", lambda q: {"query": q}, "Web search tool"))
        self.register(ToolSpec("browser_automation", "browser", lambda action: {"action": action}, "Browser automation"))
        self.register(ToolSpec("filesystem", "system", lambda path: {"path": path}, "Filesystem operations"))
        self.register(ToolSpec("api_execution", "integration", lambda req: {"request": req}, "API execution"))
        self.register(ToolSpec("database_queries", "data", lambda sql: {"sql": sql}, "Database query execution"))
        self.register(ToolSpec("code_execution", "compute", lambda code: {"code": code}, "Sandboxed code execution"))

    def get(self, name: str) -> ToolSpec:
        if name not in self._tools:
            msg = f"Tool '{name}' is not registered"
            raise KeyError(msg)
        return self._tools[name]

    def all_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def _sandboxed_handler(self, handler: ToolCallable, tool_name: str) -> ToolCallable:
        @wraps(handler)
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            result = DEFAULT_SANDBOX_RUNNER.run_callable(handler, *args, policy=SandboxPolicy(), **kwargs)
            if not result.ok:
                return {"error": f"{tool_name} sandbox error: {result.error}"}
            return result.output

        return _wrapped

    def attach_to_agent(self, agent: Any, tool_names: list[str]) -> None:
        bound = {name: self._sandboxed_handler(self.get(name).handler, name) for name in tool_names}
        setattr(agent, "tools", bound)
