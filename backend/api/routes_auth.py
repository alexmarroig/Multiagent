"""Rotas de autenticação usando Supabase Auth."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from supabase import AuthApiError

from auth.jwt_handler import create_access_token
from db.supabase_client import get_supabase

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


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
        token = create_access_token({"sub": user_id})
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()

        return AuthResponse(access_token=token, user=profile.data[0] if profile.data else {})
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
        token = create_access_token({"sub": user_id})
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()

        return AuthResponse(access_token=token, user=profile.data[0] if profile.data else {})
    except AuthApiError as exc:
        raise HTTPException(status_code=401, detail="Credenciais inválidas") from exc


@router.post("/logout")
async def logout() -> dict[str, str]:
    return {"message": "Logout realizado"}
