"""Rotas utilitárias de tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from auth.dependencies import get_current_user
from models.schemas import CallConfig, ExcelConfig, MeetingConfig, TravelConfig
from tools.browser_tools import search_hotels
from tools.circuit_breaker import CircuitOpenError, circuit_breakers
from tools.calendar_tools import schedule_meeting
from tools.excel_tools import create_excel_spreadsheet
from tools.phone_tools import make_phone_call
from security.rbac import Permission, RBACAuthorizationError, RBACResource, rbac_middleware

router = APIRouter(prefix="/api/tools", tags=["tools"])

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs")).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _authorize_tool_invocation(user: dict[str, Any], tool_name: str) -> None:
    context = rbac_middleware.context_from_user(user, fallback_roles=("operator",))
    try:
        rbac_middleware.authorize(
            context=context,
            permission=Permission.TOOL_INVOKE,
            resource=RBACResource(
                resource_type="tool",
                action="invoke",
                resource_id=tool_name,
                tenant_id=user.get("tenant_id") or user.get("organization_id"),
                scope="tenant",
            ),
        )
    except RBACAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _parse_excel_tool_result(raw_output: str) -> tuple[bool, dict[str, Any]]:
    """
    Tool pode retornar:
      1) JSON string: {"success": true, "artifact_id": "..."} ou {"artifact_path": "..."}
      2) String simples: "/app/outputs/arquivo.xlsx"
    """
    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, dict):
            return True, parsed
    except json.JSONDecodeError:
        pass

    # fallback: tratar como caminho
    return False, {"artifact_path": raw_output}


def _resolve_artifact_path(
    artifact_id: str | None = None,
    artifact_path: str | None = None,
) -> Path:
    if artifact_id:
        candidate = (OUTPUT_DIR / artifact_id).resolve()
    elif artifact_path:
        candidate = Path(artifact_path).expanduser().resolve()
    else:
        raise HTTPException(status_code=400, detail="artifact_id ou artifact_path é obrigatório")

    # garante que está dentro do OUTPUT_DIR
    try:
        candidate.relative_to(OUTPUT_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Artefato fora de outputs/") from exc

    if candidate.suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="Apenas artefatos .xlsx são suportados")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Artefato não encontrado")

    return candidate


@router.post("/excel/create")
async def create_excel(config: ExcelConfig, user: dict = Depends(get_current_user)):
    _authorize_tool_invocation(user, "create_excel_spreadsheet")
    try:
        raw_output = circuit_breakers.invoke(
            "create_excel_spreadsheet",
            create_excel_spreadsheet,
            data_json=json.dumps(config.data, ensure_ascii=False),
            title=config.title,
            filename=config.filename,
        )
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    is_json, payload = _parse_excel_tool_result(raw_output)

    # Se o tool devolve JSON com success=false
    if is_json and payload.get("success") is False:
        # garante formato coerente de erro
        raise HTTPException(status_code=400, detail=payload.get("error") or "Falha ao gerar planilha")

    # Quando for JSON: resolve artifact_id/artifact_path
    if is_json:
        path = _resolve_artifact_path(payload.get("artifact_id"), payload.get("artifact_path"))
        return FileResponse(path=path, filename=path.name, media_type=XLSX_MEDIA_TYPE)

    # Quando for string path: valida e serve (mantendo a mesma regra de outputs/)
    path = _resolve_artifact_path(artifact_path=payload.get("artifact_path"))
    return FileResponse(path=path, filename=path.name, media_type=XLSX_MEDIA_TYPE)


@router.get("/artifacts/download")
async def download_artifact(artifact_id: str | None = None, artifact_path: str | None = None):
    path = _resolve_artifact_path(artifact_id=artifact_id, artifact_path=artifact_path)
    return FileResponse(path=path, filename=path.name, media_type=XLSX_MEDIA_TYPE)


@router.post("/calendar/schedule")
async def create_meeting(config: MeetingConfig, user: dict = Depends(get_current_user)) -> dict:
    _authorize_tool_invocation(user, "schedule_meeting")
    try:
        return circuit_breakers.invoke(
            "schedule_meeting",
            schedule_meeting,
            title=config.title,
            start_datetime=config.start_datetime,
            end_datetime=config.end_datetime,
            description=config.description,
            attendees_json=json.dumps(config.attendees, ensure_ascii=False),
        )
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/phone/call")
async def phone_call(config: CallConfig, user: dict = Depends(get_current_user)) -> dict:
    _authorize_tool_invocation(user, "make_phone_call")
    try:
        return circuit_breakers.invoke(
            "make_phone_call", make_phone_call, config.to_number, config.script, config.language
        )
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/travel/search")
async def travel_search(config: TravelConfig, user: dict = Depends(get_current_user)) -> dict:
    _authorize_tool_invocation(user, "search_hotels")
    try:
        raw = circuit_breakers.invoke(
            "search_hotels",
            search_hotels,
            config.destination,
            config.checkin,
            config.checkout,
            config.adults,
        )
    except CircuitOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    parsed = json.loads(raw)
    return {"options": parsed.get("options", []), "meta": parsed}
