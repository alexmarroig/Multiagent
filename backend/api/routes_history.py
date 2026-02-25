"""Histórico de execuções por usuário."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user
from db.audit import log_audit_event
from db.supabase_client import get_supabase

router = APIRouter()


@router.get("/")
async def list_executions(
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    supabase = get_supabase()
    result = (
        supabase.table("executions")
        .select("*")
        .eq("user_id", user["id"])
        .order("started_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    log_audit_event(
        user_id=user["id"],
        action="list_runs",
        resource_type="execution",
        resource_id="*",
        metadata={"limit": limit, "offset": offset},
    )
    return {"executions": result.data, "total": len(result.data)}


@router.get("/{session_id}")
async def get_execution(session_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    supabase = get_supabase()
    result = (
        supabase.table("executions")
        .select("*")
        .eq("session_id", session_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    execution = result.data[0]
    log_audit_event(
        user_id=user["id"],
        action="read_run",
        resource_type="execution",
        resource_id=execution["id"],
        metadata={"session_id": session_id},
    )
    if execution.get("result") and execution["result"].get("artifacts"):
        log_audit_event(
            user_id=user["id"],
            action="read_artifact",
            resource_type="artifact",
            resource_id=session_id,
            metadata={"artifact_count": len(execution["result"].get("artifacts", []))},
        )
    return execution
