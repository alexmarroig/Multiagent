"""Governance approval APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from governance.control_plane import approval_queue

router = APIRouter(prefix="/governance", tags=["governance"])


class DecisionPayload(BaseModel):
    token: str
    reviewer: str
    comment: str = ""


@router.get("/pending")
async def list_pending() -> list[dict[str, Any]]:
    pending = approval_queue.pending()
    return [
        {
            "token": req.token,
            "reason": req.reason,
            "payload": req.payload,
            "reviewers": req.reviewers,
            "created_at": req.created_at,
            "audit_history": [
                {
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "actor": entry.actor,
                    "details": entry.details,
                }
                for entry in req.audit_history
            ],
        }
        for req in pending
    ]


@router.post("/approve")
async def approve_request(payload: DecisionPayload) -> dict[str, Any]:
    request = approval_queue.get(payload.token)
    if request is None:
        raise HTTPException(status_code=404, detail="Approval token not found")
    approval_queue.assign_reviewer(token=payload.token, reviewer=payload.reviewer, assigned_by=payload.reviewer)
    decision = approval_queue.record_decision(
        token=payload.token,
        decision="approved",
        reviewer=payload.reviewer,
        comment=payload.comment,
    )
    return {"token": decision.token, "status": decision.status, "resolved_at": decision.resolved_at}


@router.post("/reject")
async def reject_request(payload: DecisionPayload) -> dict[str, Any]:
    request = approval_queue.get(payload.token)
    if request is None:
        raise HTTPException(status_code=404, detail="Approval token not found")
    approval_queue.assign_reviewer(token=payload.token, reviewer=payload.reviewer, assigned_by=payload.reviewer)
    decision = approval_queue.record_decision(
        token=payload.token,
        decision="rejected",
        reviewer=payload.reviewer,
        comment=payload.comment,
    )
    return {"token": decision.token, "status": decision.status, "resolved_at": decision.resolved_at}
