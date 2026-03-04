"""Thread-safe human approval queue with audit trail."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Condition, RLock
from typing import Any, Literal

DecisionType = Literal["approved", "rejected"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AuditEntry:
    timestamp: str
    action: str
    actor: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ApprovalRequest:
    token: str
    reason: str
    payload: dict[str, Any] = field(default_factory=dict)
    reviewers: list[str] = field(default_factory=list)
    status: str = "pending"
    decision: DecisionType | None = None
    decision_by: str | None = None
    decision_comment: str = ""
    created_at: str = field(default_factory=_utc_now)
    resolved_at: str | None = None
    audit_history: list[AuditEntry] = field(default_factory=list)


class ApprovalQueue:
    """In-memory queue for approvals with blocking wait support."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._condition = Condition(self._lock)
        self._requests: dict[str, ApprovalRequest] = {}

    def submit(self, *, token: str, reason: str, payload: dict[str, Any] | None = None) -> ApprovalRequest:
        with self._condition:
            existing = self._requests.get(token)
            if existing is not None:
                return existing
            request = ApprovalRequest(token=token, reason=reason, payload=payload or {})
            request.audit_history.append(
                AuditEntry(timestamp=_utc_now(), action="submitted", actor="system", details={"reason": reason})
            )
            self._requests[token] = request
            self._condition.notify_all()
            return request

    def assign_reviewer(self, *, token: str, reviewer: str, assigned_by: str = "system") -> ApprovalRequest:
        with self._condition:
            request = self._requests[token]
            if reviewer not in request.reviewers:
                request.reviewers.append(reviewer)
                request.audit_history.append(
                    AuditEntry(
                        timestamp=_utc_now(),
                        action="reviewer_assigned",
                        actor=assigned_by,
                        details={"reviewer": reviewer},
                    )
                )
                self._condition.notify_all()
            return request

    def record_decision(
        self,
        *,
        token: str,
        decision: DecisionType,
        reviewer: str,
        comment: str = "",
    ) -> ApprovalRequest:
        with self._condition:
            request = self._requests[token]
            request.status = decision
            request.decision = decision
            request.decision_by = reviewer
            request.decision_comment = comment
            request.resolved_at = _utc_now()
            request.audit_history.append(
                AuditEntry(
                    timestamp=request.resolved_at,
                    action="decision_recorded",
                    actor=reviewer,
                    details={"decision": decision, "comment": comment},
                )
            )
            self._condition.notify_all()
            return request

    def get(self, token: str) -> ApprovalRequest | None:
        with self._lock:
            return self._requests.get(token)

    def pending(self) -> list[ApprovalRequest]:
        with self._lock:
            return [req for req in self._requests.values() if req.status == "pending"]

    def wait_for_resolution(self, token: str, timeout_seconds: float | None = None) -> ApprovalRequest:
        with self._condition:
            request = self._requests[token]
            self._condition.wait_for(lambda: request.status in {"approved", "rejected"}, timeout=timeout_seconds)
            return request


GLOBAL_APPROVAL_QUEUE = ApprovalQueue()
