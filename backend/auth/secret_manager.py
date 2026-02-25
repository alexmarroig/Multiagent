"""Provedor de segredos versionados com suporte a rotação de chaves."""

from __future__ import annotations

import os
from dataclasses import dataclass

from config import settings
from db.supabase_client import get_supabase


@dataclass
class SecretVersion:
    name: str
    value: str
    version: str


class SecretManager:
    def get_active_secret(self, name: str, env_fallback: str | None = None) -> SecretVersion:
        if settings.secret_manager_provider == "supabase":
            return self._get_from_supabase(name)

        env_name = env_fallback or name.upper()
        value = os.getenv(env_name)
        if not value:
            raise RuntimeError(f"Segredo ausente: {env_name}")
        return SecretVersion(name=name, value=value, version="env")

    def _get_from_supabase(self, name: str) -> SecretVersion:
        supabase = get_supabase()
        response = (
            supabase.table(settings.supabase_secret_table)
            .select("name,value,version")
            .eq("name", name)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        if not response.data:
            raise RuntimeError(
                f"Segredo '{name}' não encontrado na tabela {settings.supabase_secret_table}"
            )
        row = response.data[0]
        return SecretVersion(name=row["name"], value=row["value"], version=str(row["version"]))


secret_manager = SecretManager()
