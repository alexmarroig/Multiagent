from __future__ import annotations

import json
from pathlib import Path

import pytest

from governance.audit_ledger import (
    EVENT_APPROVAL_DECISION,
    EVENT_BUDGET_OVERRIDE,
    EVENT_POLICY_VIOLATION,
    EVENT_TOOL_EXECUTION,
    AuditLedger,
    AuditLedgerIntegrityError,
)


def test_records_required_governance_events(tmp_path: Path) -> None:
    ledger = AuditLedger(tmp_path / "audit.jsonl", signing_key="secret")

    ledger.record_approval_decision(actor="reviewer", token="abc", decision="approved")
    ledger.record_policy_violation(actor="policy", violations=["risk_limit_exceeded"])
    ledger.record_tool_execution(actor="executor", tool="browser.search", status="success")
    ledger.record_budget_override(actor="admin", previous_budget=5.0, new_budget=10.0, reason="incident")

    ledger.verify()

    assert len(ledger.query(event_type=EVENT_APPROVAL_DECISION)) == 1
    assert len(ledger.query(event_type=EVENT_POLICY_VIOLATION)) == 1
    assert len(ledger.query(event_type=EVENT_TOOL_EXECUTION)) == 1
    assert len(ledger.query(event_type=EVENT_BUDGET_OVERRIDE)) == 1


def test_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    ledger = AuditLedger(path, signing_key="secret")
    ledger.record_tool_execution(actor="executor", tool="runtime.run", status="success")

    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    rows[0]["details"]["status"] = "failed"
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")

    with pytest.raises(AuditLedgerIntegrityError, match="entry hash mismatch"):
        ledger.verify()


def test_query_filters_by_actor_and_content(tmp_path: Path) -> None:
    ledger = AuditLedger(tmp_path / "audit.jsonl", signing_key="secret")
    ledger.record_tool_execution(actor="alpha", tool="calendar.create", status="success")
    ledger.record_tool_execution(actor="beta", tool="finance.transfer", status="failed", metadata={"error": "blocked"})

    alpha_entries = ledger.query(event_type=EVENT_TOOL_EXECUTION, actor="alpha")
    blocked_entries = ledger.query(event_type=EVENT_TOOL_EXECUTION, contains="blocked")

    assert len(alpha_entries) == 1
    assert alpha_entries[0].details["tool"] == "calendar.create"
    assert len(blocked_entries) == 1
    assert blocked_entries[0].actor == "beta"
