"""Governance control-plane endpoints for human approvals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from governance.approval_queue import get_approval_queue

router = APIRouter(tags=["governance"])


class ApprovalDecisionRequest(BaseModel):
    token: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    comment: str | None = None


@router.get("/governance/pending")
async def list_pending_approvals() -> dict[str, list[dict[str, Any]]]:
    queue = get_approval_queue()
    return {"pending": queue.pending()}


@router.post("/governance/approve")
async def approve_request(body: ApprovalDecisionRequest) -> dict[str, Any]:
    queue = get_approval_queue()
    try:
        item = queue.record_decision(
            token=body.token,
            decision="approved",
            reviewer=body.reviewer,
            comment=body.comment,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "approved", "item": item.to_dict()}


@router.post("/governance/reject")
async def reject_request(body: ApprovalDecisionRequest) -> dict[str, Any]:
    queue = get_approval_queue()
    try:
        item = queue.record_decision(
            token=body.token,
            decision="rejected",
            reviewer=body.reviewer,
            comment=body.comment,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "rejected", "item": item.to_dict()}
