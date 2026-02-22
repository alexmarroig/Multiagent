"""Configuração centralizada de ambiente para o backend."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do backend carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    port: int = Field(default=8000, alias="PORT")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_service_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_KEY")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")

    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")

    def validate_runtime(self) -> None:
        """Falha rápido em produção quando variáveis críticas não estão definidas."""
        missing: list[str] = []

        if self.app_env == "production":
            if not self.supabase_url:
                missing.append("SUPABASE_URL")
            if not (self.supabase_service_key or self.supabase_service_role_key):
                missing.append("SUPABASE_SERVICE_KEY|SUPABASE_SERVICE_ROLE_KEY")
            if self.jwt_secret_key == "dev-secret-change-me":
                missing.append("JWT_SECRET_KEY (não pode usar valor padrão)")

        if missing:
            raise RuntimeError(f"Variáveis obrigatórias ausentes/inválidas: {', '.join(missing)}")


settings = Settings()


def is_production() -> bool:
    return settings.app_env == "production"


def current_pid() -> int:
    return os.getpid()
