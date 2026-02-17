"""WebSocket para streaming de eventos de execução."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from orchestrator.event_stream import subscribe_events

router = APIRouter(tags=["ws"])


@router.websocket("/ws/{session_id}")
async def stream_logs(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()
    try:
        async for event in subscribe_events(session_id):
            await websocket.send_json(event.model_dump(mode="json"))
            if event.event_type in {"done", "error"}:
                break
    except WebSocketDisconnect:
        return
    finally:
        await websocket.close()
