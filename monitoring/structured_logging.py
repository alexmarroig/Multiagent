"""Structured logging utilities for runtime observability hooks."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def log_event(
    logger: logging.Logger,
    *,
    component: str,
    event: str,
    severity: str = "info",
    **fields: Any,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "event": event,
        "severity": severity,
    }
    payload.update(fields)

    emitter = getattr(logger, severity.lower(), logger.info)
    emitter(json.dumps(payload, ensure_ascii=False, default=str))
