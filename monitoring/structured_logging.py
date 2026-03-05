"""Structured logging utilities for runtime observability hooks."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from monitoring.tracing import get_tracer
from security.tenant_context import current_tenant_context


def log_event(
    logger: logging.Logger,
    *,
    component: str,
    event: str,
    severity: str = "info",
    **fields: Any,
) -> None:
    tracer = get_tracer()
    trace_ctx = tracer.current_context()
    tenant_ctx = current_tenant_context()
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "event": event,
        "severity": severity,
        "trace_id": trace_ctx.trace_id if trace_ctx else None,
        "tenant_id": tenant_ctx.tenant_id if tenant_ctx else None,
        "agent_id": tenant_ctx.agent_id if tenant_ctx else None,
        "request_id": tenant_ctx.request_id if tenant_ctx else None,
        "task_id": tenant_ctx.task_id if tenant_ctx else None,
    }
    payload.update(fields)

    emitter = getattr(logger, severity.lower(), logger.info)
    emitter(json.dumps(payload, ensure_ascii=False, default=str))
