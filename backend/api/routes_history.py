"""Histórico de execuções por usuário."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user
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
    return result.data[0]
