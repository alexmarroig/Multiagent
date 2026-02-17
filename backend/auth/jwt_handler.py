"""Helpers de JWT e senha para autenticação."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRATION = int(os.getenv("JWT_EXPIRATION_MINUTES", "43200"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict[str, Any]) -> str:
    """Gera token JWT assinado com validade configurável."""
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=EXPIRATION)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    """Valida token JWT e retorna payload quando válido."""
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
