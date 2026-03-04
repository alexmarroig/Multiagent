"""Human-in-the-loop approval service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApprovalRequest:
    request_id: str
    payload: dict[str, Any]
    reason: str


class HumanApprovalService:
    def __init__(self, auto_approve: bool = True) -> None:
        self.auto_approve = auto_approve
        self._requests: list[ApprovalRequest] = []

    def request_approval(self, request_id: str, payload: dict[str, Any], reason: str) -> bool:
        self._requests.append(ApprovalRequest(request_id=request_id, payload=payload, reason=reason))
        return self.auto_approve

    def pending(self) -> list[ApprovalRequest]:
        return list(self._requests)
