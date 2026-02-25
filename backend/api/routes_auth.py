"""Rotas de autenticação usando Supabase Auth."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from supabase import AuthApiError

from auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_hashed_token,
    verify_refresh_token,
)
from auth.dependencies import get_current_user
from db.supabase_client import get_supabase

router = APIRouter()
security = HTTPBearer()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


def _store_refresh_token(user_id: str, refresh_token: str, claims: dict) -> None:
    supabase = get_supabase()
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc).isoformat()
    supabase.table("refresh_tokens").insert(
        {
            "user_id": user_id,
            "jti": claims["jti"],
            "token_hash": hash_token(refresh_token),
            "expires_at": expires_at,
            "revoked": False,
        }
    ).execute()


def _issue_auth_tokens(user_id: str) -> tuple[str, str]:
    access_token, _ = create_access_token(subject=user_id)
    refresh_token, refresh_claims = create_refresh_token(subject=user_id)
    _store_refresh_token(user_id=user_id, refresh_token=refresh_token, claims=refresh_claims)
    return access_token, refresh_token


@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest) -> AuthResponse:
    supabase = get_supabase()
    try:
        auth_response = supabase.auth.sign_up(
            {
                "email": req.email,
                "password": req.password,
                "options": {"data": {"full_name": req.full_name}},
            }
        )

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Erro ao criar usuário")

        user_id = str(auth_response.user.id)
        access_token, refresh_token = _issue_auth_tokens(user_id)
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=profile.data[0] if profile.data else {},
        )
    except AuthApiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest) -> AuthResponse:
    supabase = get_supabase()
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": req.email, "password": req.password}
        )
        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        user_id = str(auth_response.user.id)
        access_token, refresh_token = _issue_auth_tokens(user_id)
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=profile.data[0] if profile.data else {},
        )
    except AuthApiError as exc:
        raise HTTPException(status_code=401, detail="Credenciais inválidas") from exc


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(req: RefreshRequest) -> AuthResponse:
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    user_id = payload["sub"]
    jti = payload["jti"]
    supabase = get_supabase()
    token_row = (
        supabase.table("refresh_tokens")
        .select("*")
        .eq("user_id", user_id)
        .eq("jti", jti)
        .eq("revoked", False)
        .limit(1)
        .execute()
    )
    if not token_row.data:
        raise HTTPException(status_code=401, detail="Refresh token revogado")

    db_token = token_row.data[0]
    if not verify_hashed_token(req.refresh_token, db_token["token_hash"]):
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    supabase.table("refresh_tokens").update({"revoked": True}).eq("id", db_token["id"]).execute()

    access_token, refresh_token = _issue_auth_tokens(user_id)
    profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=profile.data[0] if profile.data else {},
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: dict = Depends(get_current_user),
) -> dict[str, str]:
    _ = credentials
    supabase = get_supabase()
    supabase.table("refresh_tokens").update({"revoked": True}).eq("user_id", user["id"]).execute()
    return {"message": "Logout realizado"}
