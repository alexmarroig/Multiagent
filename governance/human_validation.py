"""Configurable human validation gates with pause/resume semantics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from governance.approval_queue import ApprovalQueue


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
        self.approval_queue = approval_queue
        self.block_on_pending = block_on_pending
        self._approvals: dict[str, bool] = {}

    def grant_approval(self, token: str) -> None:
        self._approvals[token] = True

    def _require(self, token: str, reason: str) -> None:
        if not self._approvals.get(token, False):
            if self.approval_queue is not None and self.block_on_pending:
                self.approval_queue.submit(token=token, reason=reason)
                decision = self.approval_queue.wait_for_resolution(token)
                if decision.status == "approved":
                    self._approvals[token] = True
                    return
            raise HumanValidationError(f"Execution paused pending human approval ({reason}). token={token}")

    def request_approval(self, *, token: str, reason: str) -> None:
        """Trigger an explicit human approval gate for non-policy runtime safeguards."""
        self._require(token, reason)

    def validate_task(self, *, task_id: str, payload: dict[str, Any]) -> None:
        if self.gates.require_pre_execution_approval:
            self._require(f"task:{task_id}:execute", "pre_execution")

        if self.gates.require_external_api_approval and payload.get("external_api", False):
            self._require(f"task:{task_id}:external_api", "external_api")

        estimated_cost = float(payload.get("estimated_cost", 0.0))
        if self.gates.require_high_cost_approval and estimated_cost >= self.gates.high_cost_threshold:
            self._require(f"task:{task_id}:cost", "high_cost")
