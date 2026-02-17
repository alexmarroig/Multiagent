"""Ferramentas de agenda com Google Calendar."""

from __future__ import annotations

import json
import os
from datetime import datetime

from crewai_tools import tool
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


@tool("schedule_meeting")
def schedule_meeting(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    attendees_json: str = "[]",
) -> dict:
    """Cria evento no Google Calendar com link de reunião."""
    creds_path = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_JSON", "./credentials/google_calendar.json")
    attendees = json.loads(attendees_json) if attendees_json else []

    if not os.path.exists(creds_path):
        return {
            "success": True,
            "simulated": True,
            "meet_link": "https://meet.google.com/simulated-link",
            "event_link": "https://calendar.google.com/simulated-event",
            "message": "Credenciais não encontradas. Agendamento simulado.",
        }

    try:
        scopes = ["https://www.googleapis.com/auth/calendar"]
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": datetime.fromisoformat(start_datetime).isoformat(), "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": datetime.fromisoformat(end_datetime).isoformat(), "timeZone": "America/Sao_Paulo"},
            "attendees": [{"email": email} for email in attendees],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"agentos-{int(datetime.utcnow().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        created = (
            service.events()
            .insert(calendarId="primary", body=event, conferenceDataVersion=1, sendUpdates="all")
            .execute()
        )

        entry_points = created.get("conferenceData", {}).get("entryPoints", [])
        meet_link = next((x.get("uri") for x in entry_points if x.get("entryPointType") == "video"), None)
        return {"success": True, "meet_link": meet_link, "event_link": created.get("htmlLink")}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
