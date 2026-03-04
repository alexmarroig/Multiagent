"""Helpers para logs estruturados em JSON."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


def log_structured(
    logger: logging.Logger,
    message: str,
    *,
    session_id: str | None = None,
    user_id: str | None = None,
    agent_id: str | None = None,
    tool_id: str | None = None,
    **extra: Any,
) -> None:
    """Emite payload JSON com chaves padronizadas para observabilidade."""
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "session_id": session_id or "-",
        "user_id": user_id or "-",
        "agent_id": agent_id or "-",
        "tool_id": tool_id or "-",
    }
    payload.update(extra)
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))
