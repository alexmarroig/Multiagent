"""Configurable human validation gates with pause/resume semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentos.governance.approval_queue import ApprovalQueue, get_approval_queue


@dataclass(slots=True)
class ValidationGates:
    require_pre_execution_approval: bool = False
    require_external_api_approval: bool = False
    require_high_cost_approval: bool = False
    high_cost_threshold: float = 50.0


class HumanValidationError(RuntimeError):
    """Raised when execution must pause for human approval."""


class HumanValidationController:
    def __init__(
        self,
        gates: ValidationGates | None = None,
        *,
        approval_queue: ApprovalQueue | None = None,
        block_on_pending: bool = False,
    ) -> None:
        self.gates = gates or ValidationGates()
        self.approval_queue = approval_queue or get_approval_queue()
        self.block_on_pending = block_on_pending

        # local cache for granted approvals
        self._approvals: dict[str, bool] = {}

    def grant_approval(
        self,
        token: str,
        reviewer: str = "system",
        comment: str | None = None,
    ) -> None:
        """Manually grant approval."""
        self.approval_queue.submit(token=token, reason="manual_grant")

        self.approval_queue.record_decision(
            token=token,
            decision="approved",
            reviewer=reviewer,
            comment=comment or "",
        )

        self._approvals[token] = True

    def reject_approval(
        self,
        token: str,
        reviewer: str,
        comment: str | None = None,
    ) -> None:
        """Manually reject approval."""
        self.approval_queue.submit(token=token, reason="manual_reject")

        self.approval_queue.record_decision(
            token=token,
            decision="rejected",
            reviewer=reviewer,
            comment=comment or "",
        )

        self._approvals[token] = False

    def _require(
        self,
        token: str,
        reason: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Internal gate enforcement."""

        if self._approvals.get(token):
            return

        request = self.approval_queue.submit(
            token=token,
            reason=reason,
            payload=payload,
        )

        if request.status == "approved":
            self._approvals[token] = True
            return

        if request.status == "rejected":
            raise HumanValidationError(
                f"Execution blocked by human rejection ({reason}). token={token}"
            )

        if self.block_on_pending:
            decision = self.approval_queue.wait_for_resolution(token)

            if decision.status == "approved":
                self._approvals[token] = True
                return

            raise HumanValidationError(
                f"Execution blocked by human rejection ({reason}). token={token}"
            )

        raise HumanValidationError(
            f"Execution paused pending human approval ({reason}). token={token}"
        )

    def request_approval(
        self,
        *,
        token: str,
        reason: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Explicit human approval gate."""
        self._require(token, reason, payload=payload)

    def validate_task(
        self,
        *,
        task_id: str,
        payload: dict[str, Any],
    ) -> None:
        """Validate task execution against configured gates."""

        if self.gates.require_pre_execution_approval:
            self._require(
                f"task:{task_id}:execute",
                "pre_execution",
                payload=payload,
            )

        if self.gates.require_external_api_approval and payload.get("external_api", False):
            self._require(
                f"task:{task_id}:external_api",
                "external_api",
                payload=payload,
            )

        estimated_cost = float(payload.get("estimated_cost", 0.0))

        if (
            self.gates.require_high_cost_approval
            and estimated_cost >= self.gates.high_cost_threshold
        ):
            self._require(
                f"task:{task_id}:cost",
                "high_cost",
                payload=payload,
            )