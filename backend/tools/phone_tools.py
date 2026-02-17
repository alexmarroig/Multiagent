"""Ferramentas de telefonia com Twilio."""

from __future__ import annotations

import os

from crewai_tools import tool
from twilio.rest import Client


@tool("make_phone_call")
def make_phone_call(to_number: str, script: str, language: str = "pt-BR") -> dict:
    """Realiza ligação com script via TwiML."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    if not account_sid or not auth_token or not from_number:
        return {
            "success": False,
            "warning": "Credenciais Twilio não configuradas. Operação simulada.",
            "status": "simulated",
        }

    try:
        client = Client(account_sid, auth_token)
        twiml = f'<Response><Say language="{language}" voice="Polly.Camila">{script}</Say></Response>'
        call = client.calls.create(to=to_number, from_=from_number, twiml=twiml)
        return {"success": True, "call_sid": call.sid, "status": call.status}
    except Exception as exc:
        return {"success": False, "error": str(exc), "status": "failed"}
