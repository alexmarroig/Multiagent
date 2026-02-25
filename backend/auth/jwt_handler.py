"""Helpers de JWT, refresh token e senha para autenticação."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from auth.secret_manager import secret_manager
from config import settings

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"


def _base_claims(subject: str, token_type: str, expires_delta: timedelta) -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    return {
        "sub": subject,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": str(uuid4()),
        "typ": token_type,
    }


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    claims = _base_claims(
        subject=subject,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.jwt_access_expiration_minutes),
    )
    if extra_claims:
        claims.update(extra_claims)

    secret = secret_manager.get_active_secret(
        settings.jwt_access_secret_name, env_fallback="JWT_ACCESS_SECRET_KEY"
    )
    token = jwt.encode(claims, secret.value, algorithm=ALGORITHM, headers={"kid": secret.version})
    return token, claims


def create_refresh_token(subject: str) -> tuple[str, dict[str, Any]]:
    claims = _base_claims(
        subject=subject,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.jwt_refresh_expiration_days),
    )
    secret = secret_manager.get_active_secret(
        settings.jwt_refresh_secret_name, env_fallback="JWT_REFRESH_SECRET_KEY"
    )
    token = jwt.encode(claims, secret.value, algorithm=ALGORITHM, headers={"kid": secret.version})
    return token, claims


def _decode_with_secret(token: str, secret_name: str, env_fallback: str) -> dict[str, Any]:
    secret = secret_manager.get_active_secret(secret_name, env_fallback=env_fallback)
    return jwt.decode(
        token,
        secret.value,
        algorithms=[ALGORITHM],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"verify_aud": True, "verify_iss": True},
    )


def verify_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = _decode_with_secret(token, settings.jwt_access_secret_name, "JWT_ACCESS_SECRET_KEY")
        if payload.get("typ") != TokenType.ACCESS:
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    try:
        payload = _decode_with_secret(token, settings.jwt_refresh_secret_name, "JWT_REFRESH_SECRET_KEY")
        if payload.get("typ") != TokenType.REFRESH:
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_token(token: str) -> str:
    return pwd_context.hash(token)


def verify_hashed_token(token: str, hashed: str) -> bool:
    return pwd_context.verify(token, hashed)
