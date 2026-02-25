"""WebSocket para streaming de eventos de execução."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from observability.logging import log_structured
from observability.metrics import metrics_store
from orchestrator.event_stream import subscribe_events

router = APIRouter(tags=["ws"])
logger = logging.getLogger("agentos-backend")


@router.websocket("/ws/{session_id}")
async def stream_logs(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    log_structured(logger, "websocket_connected", session_id=session_id, agent_id="system")
    try:
        async for event in subscribe_events(session_id):
            await websocket.send_json(event.model_dump(mode="json"))
            if event.event_type in {"done", "error"}:
                break
    except WebSocketDisconnect:
        log_structured(logger, "websocket_disconnected", session_id=session_id, agent_id="system")
        return
    except Exception as exc:
        metrics_store.record_websocket_failure()
        log_structured(
            logger,
            "websocket_stream_error",
            session_id=session_id,
            agent_id="system",
            error=str(exc),
        )
        raise
    finally:
        await websocket.close()
