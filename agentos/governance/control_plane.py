"""Shared governance control plane wiring."""

from __future__ import annotations

from agentos.governance.approval_queue import GLOBAL_APPROVAL_QUEUE
from agentos.governance.human_validation import HumanValidationController, ValidationGates

approval_queue = GLOBAL_APPROVAL_QUEUE
validation_controller = HumanValidationController(
    ValidationGates(
        require_pre_execution_approval=True,
        require_external_api_approval=True,
        require_high_cost_approval=True,
        high_cost_threshold=10.0,
    ),
    approval_queue=approval_queue,
    block_on_pending=True,
)
