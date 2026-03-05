"""Mandatory tenant context enforcement for all runtime operations."""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: str
    agent_id: str
    request_id: str
    trace_id: str | None = None
    task_id: str | None = None


_CONTEXT: contextvars.ContextVar[TenantContext | None] = contextvars.ContextVar("tenant_context", default=None)


class TenantContextError(PermissionError):
    """Raised when a required tenant context field is missing."""


def require_tenant_context(context: TenantContext | None = None, *, strict: bool = True) -> TenantContext:
    resolved = context or _CONTEXT.get()
    if resolved is None:
        if strict:
            raise TenantContextError("tenant context missing: tenant_id, agent_id, request_id are mandatory")
        return TenantContext(tenant_id="legacy", agent_id="legacy", request_id="legacy")

    if (not resolved.tenant_id or not resolved.agent_id or not resolved.request_id) and strict:
        raise TenantContextError("tenant context missing: tenant_id, agent_id, request_id are mandatory")
    return resolved


def current_tenant_context() -> TenantContext | None:
    return _CONTEXT.get()


@contextmanager
def tenant_context_scope(context: TenantContext) -> Iterator[TenantContext]:
    require_tenant_context(context)
    token = _CONTEXT.set(context)
    try:
        yield context
    finally:
        _CONTEXT.reset(token)


def enforce_context_in_metadata(metadata: dict[str, str], *, context: TenantContext | None = None, strict: bool = True) -> dict[str, str]:
    resolved = require_tenant_context(context, strict=strict)
    metadata.setdefault("tenant_id", resolved.tenant_id)
    metadata.setdefault("agent_id", resolved.agent_id)
    metadata.setdefault("request_id", resolved.request_id)
    if resolved.trace_id:
        metadata.setdefault("trace_id", resolved.trace_id)
    if resolved.task_id:
        metadata.setdefault("task_id", resolved.task_id)
    return metadata
