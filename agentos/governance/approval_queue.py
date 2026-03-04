from __future__ import annotations

from dataclasses import dataclass, field
from threading import Condition, RLock
from typing import Any, Literal

from agentos.governance.approval_store import ApprovalStore

DecisionType = Literal["approved", "rejected"]


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
    created_at: str = ""
    resolved_at: str | None = None
    audit_history: list[AuditEntry] = field(default_factory=list)


class ApprovalQueue:
    """Thread-safe approval queue persisted via ApprovalStore."""

    def __init__(self, store: ApprovalStore | None = None) -> None:
        self._lock = RLock()
        self._condition = Condition(self._lock)
        self._store = store or ApprovalStore()
        self._reviewers: dict[str, list[str]] = {}

    def submit(self, *, token: str, reason: str, payload: dict[str, Any] | None = None) -> ApprovalRequest:
        with self._condition:
            self._store.create(token=token, reason=reason, payload=payload or {})
            self._condition.notify_all()
            return self.get(token)  # type: ignore[return-value]

    def assign_reviewer(self, *, token: str, reviewer: str, assigned_by: str = "system") -> ApprovalRequest:
        with self._condition:
            reviewers = self._reviewers.setdefault(token, [])
            if reviewer not in reviewers:
                reviewers.append(reviewer)
                self._store.add_history(token=token, action="reviewer_assigned", actor=assigned_by, details={"reviewer": reviewer})
                self._condition.notify_all()
            return self.get(token)  # type: ignore[return-value]

    def record_decision(self, *, token: str, decision: DecisionType, reviewer: str, comment: str = "") -> ApprovalRequest:
        with self._condition:
            self._store.record_decision(token=token, decision=decision, reviewer=reviewer, comment=comment)
            self._condition.notify_all()
            return self.get(token)  # type: ignore[return-value]

    def get(self, token: str) -> ApprovalRequest | None:
        with self._lock:
            try:
                record = self._store.get(token)
            except KeyError:
                return None
            history = [AuditEntry(timestamp=h["created_at"], action=h["action"], actor=h["actor"], details=h["details"]) for h in self._store.history(token)]
            return ApprovalRequest(
                token=record.token,
                reason=record.reason,
                payload=record.payload,
                reviewers=list(self._reviewers.get(token, [])),
                status=record.status,
                decision=record.decision,  # type: ignore[assignment]
                decision_by=record.decision_by,
                decision_comment=record.decision_comment,
                created_at=record.created_at,
                resolved_at=record.resolved_at,
                audit_history=history,
            )

    def pending(self) -> list[ApprovalRequest]:
        with self._lock:
            return [self.get(record.token) for record in self._store.pending() if self.get(record.token) is not None]  # type: ignore[misc]

    def wait_for_resolution(self, token: str, timeout_seconds: float | None = None) -> ApprovalRequest:
        with self._condition:
            self._condition.wait_for(lambda: (req := self.get(token)) is not None and req.status in {"approved", "rejected"}, timeout=timeout_seconds)
            request = self.get(token)
            if request is None:
                raise KeyError(token)
            return request


GLOBAL_APPROVAL_QUEUE = ApprovalQueue()


def get_approval_queue() -> ApprovalQueue:
    return GLOBAL_APPROVAL_QUEUE
