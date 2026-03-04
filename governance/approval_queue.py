"""Human governance approval queue with reviewer assignment and audit trail."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Literal

Decision = Literal["approved", "rejected"]


@dataclass(slots=True)
class AuditEntry:
    token: str
    action: str
    actor: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ApprovalItem:
    token: str
    reason: str
    status: str = "pending"
    payload: dict[str, Any] = field(default_factory=dict)
    assigned_reviewer: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: str | None = None
    decision_comment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ApprovalQueue:
    def __init__(self) -> None:
        self._items: dict[str, ApprovalItem] = {}
        self._audit: list[AuditEntry] = []
        self._lock = Lock()

    def request_approval(
        self,
        *,
        token: str,
        reason: str,
        payload: dict[str, Any] | None = None,
        reviewer: str | None = None,
    ) -> ApprovalItem:
        with self._lock:
            item = self._items.get(token)
            if item is None:
                item = ApprovalItem(token=token, reason=reason, payload=payload or {}, assigned_reviewer=reviewer)
                self._items[token] = item
                self._append_audit(token, "requested", actor="system", metadata={"reason": reason})
            elif reviewer and item.assigned_reviewer != reviewer:
                item.assigned_reviewer = reviewer
                self._append_audit(token, "reviewer_assigned", actor="system", metadata={"reviewer": reviewer})
            return item

    def assign_reviewer(self, token: str, reviewer: str, actor: str = "system") -> ApprovalItem:
        with self._lock:
            item = self._require_item(token)
            item.assigned_reviewer = reviewer
            self._append_audit(token, "reviewer_assigned", actor=actor, metadata={"reviewer": reviewer})
            return item

    def record_decision(
        self,
        *,
        token: str,
        decision: Decision,
        reviewer: str,
        comment: str | None = None,
    ) -> ApprovalItem:
        with self._lock:
            item = self._require_item(token)
            item.status = decision
            item.assigned_reviewer = reviewer
            item.decision_comment = comment
            item.resolved_at = datetime.now(timezone.utc).isoformat()
            self._append_audit(
                token,
                action="decision_recorded",
                actor=reviewer,
                metadata={"decision": decision, "comment": comment or ""},
            )
            return item

    def get(self, token: str) -> ApprovalItem | None:
        with self._lock:
            return self._items.get(token)

    def pending(self) -> list[dict[str, Any]]:
        with self._lock:
            return [item.to_dict() for item in self._items.values() if item.status == "pending"]

    def audit_history(self, token: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            entries = self._audit if token is None else [entry for entry in self._audit if entry.token == token]
            return [asdict(entry) for entry in entries]

    def _require_item(self, token: str) -> ApprovalItem:
        item = self._items.get(token)
        if item is None:
            raise KeyError(f"Unknown approval token: {token}")
        return item

    def _append_audit(self, token: str, action: str, actor: str, metadata: dict[str, Any] | None = None) -> None:
        self._audit.append(
            AuditEntry(
                token=token,
                action=action,
                actor=actor,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata=metadata or {},
            )
        )


_APPROVAL_QUEUE = ApprovalQueue()


def get_approval_queue() -> ApprovalQueue:
    return _APPROVAL_QUEUE
