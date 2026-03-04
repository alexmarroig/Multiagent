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
    jwt_issuer: str = Field(default="multiagent-backend", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="multiagent-clients", alias="JWT_AUDIENCE")
    jwt_access_expiration_minutes: int = Field(default=15, alias="JWT_ACCESS_EXPIRATION_MINUTES")
    jwt_refresh_expiration_days: int = Field(default=14, alias="JWT_REFRESH_EXPIRATION_DAYS")

    secret_manager_provider: Literal["env", "supabase"] = Field(
        default="env", alias="SECRET_MANAGER_PROVIDER"
    )
    supabase_secret_table: str = Field(default="secret_versions", alias="SUPABASE_SECRET_TABLE")
    jwt_access_secret_name: str = Field(default="jwt_access_signing_key", alias="JWT_ACCESS_SECRET_NAME")
    jwt_refresh_secret_name: str = Field(default="jwt_refresh_signing_key", alias="JWT_REFRESH_SECRET_NAME")

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
            if self.secret_manager_provider == "env":
                missing.append("SECRET_MANAGER_PROVIDER (use supabase em produção para rotação)")

        if missing:
            raise RuntimeError(f"Variáveis obrigatórias ausentes/inválidas: {', '.join(missing)}")


settings = Settings()


def is_production() -> bool:
    return settings.app_env == "production"


def current_pid() -> int:
    return os.getpid()
