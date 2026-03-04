"""Runtime tool resolution and adapters for CrewAI agents."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from agentos.core.execution_gateway import ExecutionGateway, GatewayPolicy
from agentos.backend.models.schemas import NodeConfig
from agentos.backend.tools.browser_tools import browse_website, search_hotels
from agentos.backend.tools.circuit_breaker import CircuitOpenError, circuit_breakers
from agentos.backend.tools.excel_tools import create_excel_spreadsheet
from agentos.backend.tools.finance_tools import get_stock_data
from agentos.backend.tools.sandbox_runner import SandboxPolicy
from agentos.backend.tools.search_tools import web_search
from agentos.backend.tools.tool_ids import normalize_tool_ids

ToolFn = Callable[..., str]

# workspace root for filesystem tools
ALLOWED_FILESYSTEM_ROOT = Path("/workspace").resolve()

# blocked hosts for API calls (basic SSRF protection)
BLOCKED_API_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}

TOOL_SANDBOX_POLICIES: dict[str, SandboxPolicy] = {
    "web_search": SandboxPolicy(network_enabled=True),
    "browse_website": SandboxPolicy(network_enabled=True),
    "get_stock_data": SandboxPolicy(network_enabled=True),
    "search_hotels": SandboxPolicy(network_enabled=True),
    "api_call": SandboxPolicy(network_enabled=True),
    "create_excel_spreadsheet": SandboxPolicy(network_enabled=False),
    "filesystem_read": SandboxPolicy(network_enabled=False),
    "filesystem_write": SandboxPolicy(network_enabled=False),
    "database_query": SandboxPolicy(network_enabled=False),
}


def _filesystem_read(path: str) -> str:
    try:
        resolved = Path(path).expanduser().resolve()

        if not resolved.is_relative_to(ALLOWED_FILESYSTEM_ROOT):
            return "filesystem_read error: path outside allowed workspace"

        return resolved.read_text(encoding="utf-8")[:15000]

    except Exception as exc:
        return f"filesystem_read error: {exc}"


def _filesystem_write(path: str, content: str) -> str:
    try:
        resolved = Path(path).expanduser().resolve()

        if not resolved.is_relative_to(ALLOWED_FILESYSTEM_ROOT):
            return "filesystem_write error: path outside allowed workspace"

        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

        return f"saved:{resolved}"

    except Exception as exc:
        return f"filesystem_write error: {exc}"


def _api_call(url: str, method: str = "GET", payload_json: str = "") -> str:
    parsed = urlparse(url)

    if parsed.hostname in BLOCKED_API_HOSTS:
        return "api_call error: blocked host"

    payload: dict[str, Any] | None = None

    if payload_json:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            return "api_call error: payload_json must be valid JSON"

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(
                method.upper(),
                url,
                json=payload,
            )

            headers = dict(list(response.headers.items())[:50])

            return json.dumps(
                {
                    "status_code": response.status_code,
                    "headers": headers,
                    "body": response.text[:10000],
                },
                ensure_ascii=False,
            )

    except Exception as exc:
        return f"api_call error: {exc}"


def _database_query(sql: str, database_path: str = "") -> str:
    sql_clean = sql.strip().lower()

    if not sql_clean.startswith("select"):
        return "database_query error: only SELECT statements allowed"

    db_path = database_path or ":memory:"

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)

            rows = cursor.fetchmany(200)
            columns = [item[0] for item in (cursor.description or [])]

        return json.dumps(
            {
                "columns": columns,
                "rows": rows,
            },
            ensure_ascii=False,
        )

    except Exception as exc:
        return f"database_query error: {exc}"


def _travel_search(destination: str, checkin: str, checkout: str, guests: int = 2) -> str:
    return search_hotels(
        destination=destination,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
    )


TOOL_REGISTRY: dict[str, list[tuple[str, ToolFn]]] = {
    "search": [("web_search", web_search)],
    "browser": [("browse_website", browse_website)],
    "excel": [("create_excel_spreadsheet", create_excel_spreadsheet)],
    "finance": [("get_stock_data", get_stock_data)],
    "travel": [("search_hotels", _travel_search)],
    "filesystem": [
        ("filesystem_read", _filesystem_read),
        ("filesystem_write", _filesystem_write),
    ],
    "api": [("api_call", _api_call)],
    "database": [("database_query", _database_query)],
}


def _gateway() -> ExecutionGateway:
    return ExecutionGateway(
        policy=GatewayPolicy(
            require_approval_categories={"integration"},
            blocked_tools=set(),
            max_tool_cost=500.0,
            max_risk_level="high",
        )
    )


def _guarded_tool(tool_name: str, tool_callable: ToolFn, gateway: ExecutionGateway) -> ToolFn:
    def _wrapped(*args: Any, **kwargs: Any) -> str:
        estimated_cost = float(kwargs.pop("estimated_cost", 0.0) or 0.0)

        try:
            return circuit_breakers.invoke(
                tool_name,
                lambda: str(
                    gateway.execute_agent_action(
                        tool_name=tool_name,
                        category="integration" if tool_name == "api_call" else "tool",
                        handler=tool_callable,
                        args=args,
                        kwargs=kwargs,
                        estimated_cost=estimated_cost,
                        risk_level="medium" if tool_name == "api_call" else "low",
                        sandbox_policy=TOOL_SANDBOX_POLICIES.get(tool_name, SandboxPolicy(network_enabled=False)),
                    )
                ),
            )
        except CircuitOpenError as exc:
            return f"{tool_name} disabled by circuit breaker: {exc}"
        except Exception as exc:  # noqa: BLE001
            return str(exc)

    _wrapped.__name__ = tool_name

    return _wrapped


def resolve_tools(agent_config: NodeConfig) -> list[Any]:
    """Resolve runtime tools for an agent config.

    Returns CrewAI-compatible callable tools.
    """

    requested = list(agent_config.tools) + ["filesystem", "api", "database"]

    normalized, _ = normalize_tool_ids(requested)

    resolved: list[Any] = []
    seen: set[str] = set()
    gateway = _gateway()

    for tool_id in normalized:
        for tool_name, tool_callable in TOOL_REGISTRY.get(tool_id, []):
            if tool_name in seen:
                continue

            resolved.append(_guarded_tool(tool_name, tool_callable, gateway))
            seen.add(tool_name)

    return resolved
