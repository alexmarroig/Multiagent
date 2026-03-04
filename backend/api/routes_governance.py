"""Governance control-plane endpoints for human approvals."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user
from governance.control_plane import approval_queue
from security.rbac import Permission, RBACAuthorizationError, RBACResource, rbac_middleware

router = APIRouter(prefix="/governance", tags=["governance"])


class DecisionPayload(BaseModel):
    token: str
    reviewer: str
    comment: str = ""


def _authorize_governance(user: dict[str, Any], permission: Permission, action: str) -> None:
    context = rbac_middleware.context_from_user(user, fallback_roles=("auditor",))
    try:
        rbac_middleware.authorize(
            context=context,
            permission=permission,
            resource=RBACResource(
                resource_type="governance",
                action=action,
                tenant_id=user.get("tenant_id") or user.get("organization_id"),
                scope="tenant",
            ),
        )
    except RBACAuthorizationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/pending")
async def list_pending(user: dict = Depends(get_current_user)) -> list[dict[str, Any]]:
    _authorize_governance(user, Permission.GOVERNANCE_READ, "list_pending")
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
async def approve_request(payload: DecisionPayload, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    _authorize_governance(user, Permission.GOVERNANCE_DECIDE, "approve")
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
async def reject_request(payload: DecisionPayload, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    _authorize_governance(user, Permission.GOVERNANCE_DECIDE, "reject")
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
