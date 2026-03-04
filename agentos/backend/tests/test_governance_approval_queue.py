from __future__ import annotations

import threading
import time

from agentos.governance.approval_queue import ApprovalQueue
from agentos.governance.human_validation import HumanValidationController, HumanValidationError, ValidationGates


def test_approval_queue_records_pending_and_audit() -> None:
    queue = ApprovalQueue()
    req = queue.submit(token="task:1:execute", reason="pre_execution", payload={"task": "demo"})
    assert req.status == "pending"
    assert req.audit_history[0].action == "submitted"
    assert queue.pending()[0].token == "task:1:execute"


def test_human_validation_blocks_until_approval_is_resolved() -> None:
    queue = ApprovalQueue()
    controller = HumanValidationController(
        ValidationGates(require_pre_execution_approval=True),
        approval_queue=queue,
        block_on_pending=True,
    )

    result: dict[str, str] = {}

    def worker() -> None:
        try:
            controller.validate_task(task_id="42", payload={})
            result["status"] = "approved"
        except HumanValidationError:
            result["status"] = "rejected"

    thread = threading.Thread(target=worker)
    thread.start()

    time.sleep(0.1)
    assert queue.pending()[0].token == "task:42:execute"

    queue.assign_reviewer(token="task:42:execute", reviewer="alice")
    queue.record_decision(token="task:42:execute", decision="approved", reviewer="alice")

    thread.join(timeout=2)
    assert result["status"] == "approved"


def test_human_validation_raises_when_rejected() -> None:
    queue = ApprovalQueue()
    controller = HumanValidationController(
        ValidationGates(require_pre_execution_approval=True),
        approval_queue=queue,
        block_on_pending=True,
    )

    result: dict[str, str] = {}

    def worker() -> None:
        try:
            controller.validate_task(task_id="99", payload={})
            result["status"] = "approved"
        except HumanValidationError:
            result["status"] = "rejected"

    thread = threading.Thread(target=worker)
    thread.start()

    time.sleep(0.1)
    queue.assign_reviewer(token="task:99:execute", reviewer="bob")
    queue.record_decision(token="task:99:execute", decision="rejected", reviewer="bob", comment="risk too high")

    thread.join(timeout=2)
    assert result["status"] == "rejected"
