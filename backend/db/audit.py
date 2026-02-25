"""Utilitários para trilha de auditoria."""

from __future__ import annotations

from typing import Any

from db.supabase_client import get_supabase


def log_audit_event(*, user_id: str, action: str, resource_type: str, resource_id: str, metadata: dict[str, Any] | None = None) -> None:
    supabase = get_supabase()
    supabase.table("audit_logs").insert(
        {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "metadata": metadata or {},
        }
    ).execute()
