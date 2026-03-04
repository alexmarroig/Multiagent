"""Runtime tool resolution and adapters for CrewAI agents."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from governance.human_validation import HumanValidationController, HumanValidationError, ValidationGates
from models.schemas import NodeConfig
from tools.browser_tools import browse_website, search_hotels
from tools.circuit_breaker import CircuitOpenError, circuit_breakers
from tools.excel_tools import create_excel_spreadsheet
from tools.finance_tools import get_stock_data
from tools.search_tools import web_search
from tools.sandbox_runner import DEFAULT_SANDBOX_RUNNER, SandboxPolicy
from tools.tool_ids import normalize_tool_ids

ToolFn = Callable[..., str]

# workspace root for filesystem tools
ALLOWED_FILESYSTEM_ROOT = Path("/workspace").resolve()

# blocked hosts for API calls (basic SSRF protection)
BLOCKED_API_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}

HUMAN_VALIDATION = HumanValidationController(
    ValidationGates(
        require_external_api_approval=True,
        require_high_cost_approval=True,
        high_cost_threshold=100.0,
    )
)


def _approval_token(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"


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

    token = _approval_token("external_api", method.upper(), url)

    try:
        HUMAN_VALIDATION.request_approval(
            token=token,
            reason="external_api",
            payload={
                "url": url,
                "method": method.upper(),
                "operation": "api_call",
            },
        )

    except HumanValidationError as exc:
        return str(exc)

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


def _guarded_tool(tool_name: str, tool_callable: ToolFn) -> ToolFn:
    def _wrapped(*args: Any, **kwargs: Any) -> str:

        estimated_cost = float(kwargs.pop("estimated_cost", 0.0) or 0.0)

        if estimated_cost >= HUMAN_VALIDATION.gates.high_cost_threshold:

            token = _approval_token(
                "high_cost",
                tool_name,
                str(estimated_cost),
            )

            try:
                HUMAN_VALIDATION.request_approval(
                    token=token,
                    reason="high_cost",
                    payload={
                        "tool": tool_name,
                        "estimated_cost": estimated_cost,
                        "operation": "tool_invoke",
                    },
                )

            except HumanValidationError as exc:
                return str(exc)

        try:

            sandbox_policy = TOOL_SANDBOX_POLICIES.get(
                tool_name,
                SandboxPolicy(network_enabled=False),
            )

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

            return circuit_breakers.invoke(
                tool_name,
                _sandbox_invocation,
            )

        except CircuitOpenError as exc:
            return f"{tool_name} disabled by circuit breaker: {exc}"

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

    for tool_id in normalized:

        for tool_name, tool_callable in TOOL_REGISTRY.get(tool_id, []):

            if tool_name in seen:
                continue

            resolved.append(
                _guarded_tool(
                    tool_name,
                    tool_callable,
                )
            )

            seen.add(tool_name)

    return resolved