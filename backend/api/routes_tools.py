"""Rotas utilitárias de tools."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from models.schemas import CallConfig, ExcelConfig, MeetingConfig, TravelConfig
from tools.browser_tools import search_hotels
from tools.calendar_tools import schedule_meeting
from tools.excel_tools import create_excel_spreadsheet
from tools.phone_tools import make_phone_call

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.post("/excel/create")
async def create_excel(config: ExcelConfig):
    output = create_excel_spreadsheet(
        data_json=json.dumps(config.data, ensure_ascii=False),
        title=config.title,
        filename=config.filename,
    )
    path = Path(output)
    if path.exists():
        return FileResponse(path=path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return {"success": False, "error": output}


@router.post("/calendar/schedule")
async def create_meeting(config: MeetingConfig) -> dict:
    result = schedule_meeting(
        title=config.title,
        start_datetime=config.start_datetime,
        end_datetime=config.end_datetime,
        description=config.description,
        attendees_json=json.dumps(config.attendees, ensure_ascii=False),
    )
    return result


@router.post("/phone/call")
async def phone_call(config: CallConfig) -> dict:
    return make_phone_call(config.to_number, config.script, config.language)


@router.post("/travel/search")
async def travel_search(config: TravelConfig) -> dict:
    parsed = json.loads(search_hotels(config.destination, config.checkin, config.checkout, config.adults))
    return {"options": parsed.get("options", []), "meta": parsed}
