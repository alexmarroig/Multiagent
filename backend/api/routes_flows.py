"""CRUD de fluxos persistidos no Supabase."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user
from db.supabase_client import get_supabase

router = APIRouter()


class FlowCreate(BaseModel):
    name: str
    description: str = ""
    config: dict[str, Any]
    is_template: bool = False
    is_public: bool = False


class FlowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None
    is_public: bool | None = None


@router.get("/")
async def list_flows(user: dict = Depends(get_current_user)) -> dict[str, list[dict[str, Any]]]:
    supabase = get_supabase()
    result = (
        supabase.table("flows")
        .select("*")
        .or_(f"user_id.eq.{user['id']},is_public.eq.true")
        .order("created_at", desc=True)
        .execute()
    )
    return {"flows": result.data}


@router.get("/{flow_id}")
async def get_flow(flow_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    supabase = get_supabase()
    result = supabase.table("flows").select("*").eq("id", flow_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Fluxo não encontrado")

    flow = result.data[0]
    if flow["user_id"] != user["id"] and not flow.get("is_public"):
        raise HTTPException(status_code=403, detail="Acesso negado")
    return flow


@router.post("/")
async def create_flow(flow: FlowCreate, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    supabase = get_supabase()
    result = (
        supabase.table("flows")
        .insert(
            {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "name": flow.name,
                "description": flow.description,
                "config": flow.config,
                "is_template": flow.is_template,
                "is_public": flow.is_public,
            }
        )
        .execute()
    )
    return result.data[0]


@router.patch("/{flow_id}")
async def update_flow(
    flow_id: str,
    updates: FlowUpdate,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    supabase = get_supabase()
    existing = supabase.table("flows").select("*").eq("id", flow_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    update_data = updates.model_dump(exclude_unset=True)
    result = supabase.table("flows").update(update_data).eq("id", flow_id).execute()
    return result.data[0]


@router.delete("/{flow_id}")
async def delete_flow(flow_id: str, user: dict = Depends(get_current_user)) -> dict[str, str]:
    supabase = get_supabase()
    existing = supabase.table("flows").select("*").eq("id", flow_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    supabase.table("flows").delete().eq("id", flow_id).execute()
    return {"message": "Fluxo deletado"}
