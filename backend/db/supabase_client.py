"""Cliente Supabase compartilhado para acesso ao banco/auth."""

from __future__ import annotations

import os

from supabase import Client, create_client


_supabase: Client | None = None


def get_supabase() -> Client:
    """Retorna cliente Supabase singleton com service role key."""
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL/SUPABASE_SERVICE_KEY não configurados.")
        _supabase = create_client(url, key)
    return _supabase
