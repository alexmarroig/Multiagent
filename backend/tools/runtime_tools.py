"""Runtime tool resolution and adapters for CrewAI agents."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

import httpx

from models.schemas import NodeConfig
from tools.browser_tools import browse_website
from tools.circuit_breaker import CircuitOpenError, circuit_breakers
from tools.excel_tools import create_excel_spreadsheet
from tools.finance_tools import get_stock_data
from tools.search_tools import web_search
from tools.sandbox_runner import DEFAULT_SANDBOX_RUNNER, SandboxPolicy
from tools.tool_ids import normalize_tool_ids

ToolFn = Callable[..., str]


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
        return resolved.read_text(encoding="utf-8")[:15000]
    except Exception as exc:
        return f"filesystem_read error: {exc}"


def _filesystem_write(path: str, content: str) -> str:
    try:
        resolved = Path(path).expanduser().resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return f"saved:{resolved}"
    except Exception as exc:
        return f"filesystem_write error: {exc}"


def _api_call(url: str, method: str = "GET", payload_json: str = "") -> str:
    payload: dict[str, Any] | None = None
    if payload_json:
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            return "api_call error: payload_json must be valid JSON"

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.request(method.upper(), url, json=payload)
            return json.dumps(
                {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:10000],
                },
                ensure_ascii=False,
            )
    except Exception as exc:
        return f"api_call error: {exc}"


def _database_query(sql: str, database_path: str = "") -> str:
    db_path = database_path or ":memory:"
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchmany(200)
            columns = [item[0] for item in (cursor.description or [])]
            conn.commit()
        return json.dumps({"columns": columns, "rows": rows}, ensure_ascii=False)
    except Exception as exc:
        return f"database_query error: {exc}"


def _travel_search(destination: str, checkin: str, checkout: str, guests: int = 2) -> str:
    from tools.browser_tools import search_hotels

    return search_hotels(destination=destination, checkin=checkin, checkout=checkout, guests=guests)


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


def _guarded_tool(tool_name: str, tool_callable: ToolFn) -> ToolFn:
    def _wrapped(*args: Any, **kwargs: Any) -> str:
        try:
            sandbox_policy = TOOL_SANDBOX_POLICIES.get(tool_name, SandboxPolicy())

            def _sandbox_invocation() -> str:
                sandbox_result = DEFAULT_SANDBOX_RUNNER.run_callable(
                    tool_callable,
                    *args,
                    policy=sandbox_policy,
                    **kwargs,
                )
                if not sandbox_result.ok:
                    return f"{tool_name} sandbox error: {sandbox_result.error}"
                return str(sandbox_result.output)

            return circuit_breakers.invoke(tool_name, _sandbox_invocation)
        except CircuitOpenError as exc:
            return f"{tool_name} disabled by circuit breaker: {exc}"

    _wrapped.__name__ = tool_name
    return _wrapped


def resolve_tools(agent_config: NodeConfig) -> list[Any]:
    """Resolve runtime tools for an agent config.

    Returns CrewAI-compatible callable tools.
    """
    requested = list(agent_config.tools)
    requested.extend(["filesystem", "api", "database"])
    normalized, _ = normalize_tool_ids(requested)

    resolved: list[Any] = []
    seen: set[str] = set()

    for tool_id in normalized + ["filesystem", "api", "database"]:
        for tool_name, tool_callable in TOOL_REGISTRY.get(tool_id, []):
            if tool_name in seen:
                continue
            resolved.append(_guarded_tool(tool_name, tool_callable))
            seen.add(tool_name)

    return resolved
