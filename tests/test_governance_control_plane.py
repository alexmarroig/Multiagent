from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agentos.backend.api.routes_governance import router as governance_router
from agentos.governance.approval_queue import ApprovalQueue
from agentos.governance.human_validation import HumanValidationController, HumanValidationError, ValidationGates


def test_human_validation_pauses_and_resumes_with_queue_decision() -> None:
    queue = ApprovalQueue()
    validation = HumanValidationController(
        ValidationGates(require_pre_execution_approval=True, require_external_api_approval=True),
        approval_queue=queue,
    )

    payload = {"external_api": True, "estimated_cost": 2}
    try:
        validation.validate_task(task_id="T-1", payload=payload)
    except HumanValidationError as exc:
        assert "paused pending human approval" in str(exc)
    else:
        raise AssertionError("Task execution should pause until approval is resolved")

    assert len(queue.pending()) == 1
    queue.record_decision(token="task:T-1:execute", decision="approved", reviewer="reviewer-1")

    try:
        validation.validate_task(task_id="T-1", payload=payload)
    except HumanValidationError as exc:
        assert "external_api" in str(exc)
    else:
        raise AssertionError("External API gate should also pause until explicit approval")


def test_governance_routes_pending_and_decisions() -> None:
    app = FastAPI()
    app.include_router(governance_router)
    client = TestClient(app)

    queue = ApprovalQueue()
    queue.request_approval(token="task:demo:execute", reason="pre_execution", payload={"task": "demo"})

    # Patch singleton through module attribute for deterministic test isolation.
    import agentos.backend.api.routes_governance as routes

    routes.get_approval_queue = lambda: queue  # type: ignore[assignment]

    pending = client.get("/governance/pending")
    assert pending.status_code == 200
    assert pending.json()["pending"][0]["token"] == "task:demo:execute"

    approved = client.post(
        "/governance/approve",
        json={"token": "task:demo:execute", "reviewer": "alice", "comment": "looks good"},
    )
    assert approved.status_code == 200
    assert approved.json()["item"]["status"] == "approved"

    history = queue.audit_history("task:demo:execute")
    assert any(entry["action"] == "decision_recorded" for entry in history)
    assert json.dumps(history)
