"""Immutable governance audit ledger with signed, append-only entries."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_APPROVAL_DECISION = "approval_decision"
EVENT_POLICY_VIOLATION = "policy_violation"
EVENT_TOOL_EXECUTION = "tool_execution"
EVENT_BUDGET_OVERRIDE = "budget_override"


@dataclass(slots=True)
class AuditEntry:
    index: int
    timestamp: str
    event_type: str
    actor: str
    details: dict[str, Any]
    previous_hash: str
    entry_hash: str
    signature: str


class AuditLedgerIntegrityError(RuntimeError):
    """Raised when an audit ledger entry cannot be validated."""


class AuditLedger:
    """Append-only tamper-evident audit ledger for governance events.

    Entries are chained by hash and signed with HMAC so any mutation, deletion,
    or insertion is detectable during verification.
    """

    def __init__(
        self,
        ledger_path: str = "governance_audit_ledger.jsonl",
        *,
        signing_key: str | bytes,
        max_future_skew_seconds: int = 60,
    ) -> None:
        if not signing_key:
            raise ValueError("signing_key is required")

        self.ledger_path = Path(ledger_path)
        self.max_future_skew_seconds = max_future_skew_seconds
        self._signing_key = signing_key.encode("utf-8") if isinstance(signing_key, str) else signing_key
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def record_approval_decision(
        self,
        *,
        actor: str,
        token: str,
        decision: str,
        comment: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        return self.append(
            event_type=EVENT_APPROVAL_DECISION,
            actor=actor,
            details={"token": token, "decision": decision, "comment": comment, "metadata": metadata or {}},
        )

    def record_policy_violation(
        self,
        *,
        actor: str,
        violations: list[str],
        task: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        return self.append(
            event_type=EVENT_POLICY_VIOLATION,
            actor=actor,
            details={"violations": violations, "task": task or {}, "metadata": metadata or {}},
        )

    def record_tool_execution(
        self,
        *,
        actor: str,
        tool: str,
        status: str,
        duration_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        return self.append(
            event_type=EVENT_TOOL_EXECUTION,
            actor=actor,
            details={
                "tool": tool,
                "status": status,
                "duration_ms": duration_ms,
                "metadata": metadata or {},
            },
        )

    def record_budget_override(
        self,
        *,
        actor: str,
        previous_budget: float,
        new_budget: float,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        return self.append(
            event_type=EVENT_BUDGET_OVERRIDE,
            actor=actor,
            details={
                "previous_budget": previous_budget,
                "new_budget": new_budget,
                "reason": reason,
                "metadata": metadata or {},
            },
        )

    def append(self, *, event_type: str, actor: str, details: dict[str, Any]) -> AuditEntry:
        entries = self._load_entries()
        index = len(entries)
        previous_hash = entries[-1]["entry_hash"] if entries else "GENESIS"

        timestamp = datetime.now(timezone.utc)
        if entries:
            previous_ts = self._parse_timestamp(entries[-1]["timestamp"])
            if timestamp < previous_ts:
                raise AuditLedgerIntegrityError("timestamp regression detected while appending")

        payload = {
            "index": index,
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "actor": actor,
            "details": details,
            "previous_hash": previous_hash,
        }
        canonical = self._canonical_json(payload)
        entry_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        signature = self._sign(entry_hash)

        record = {
            **payload,
            "entry_hash": entry_hash,
            "signature": signature,
        }

        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True) + "\n")
            f.flush()

        return self._row_to_entry(record)

    def verify(self) -> None:
        entries = self._load_entries()
        previous_hash = "GENESIS"
        previous_ts: datetime | None = None
        now = datetime.now(timezone.utc)

        for i, row in enumerate(entries):
            if row.get("index") != i:
                raise AuditLedgerIntegrityError(f"entry index mismatch at position {i}")
            if row.get("previous_hash") != previous_hash:
                raise AuditLedgerIntegrityError(f"hash chain broken at index {i}")

            ts = self._parse_timestamp(row["timestamp"])
            if previous_ts is not None and ts < previous_ts:
                raise AuditLedgerIntegrityError(f"timestamp regression at index {i}")
            if (ts - now).total_seconds() > self.max_future_skew_seconds:
                raise AuditLedgerIntegrityError(f"timestamp integrity violation at index {i}")

            payload = {
                "index": row["index"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "actor": row["actor"],
                "details": row["details"],
                "previous_hash": row["previous_hash"],
            }
            canonical = self._canonical_json(payload)
            expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if row.get("entry_hash") != expected_hash:
                raise AuditLedgerIntegrityError(f"entry hash mismatch at index {i}")
            if not hmac.compare_digest(row.get("signature", ""), self._sign(expected_hash)):
                raise AuditLedgerIntegrityError(f"signature mismatch at index {i}")

            previous_hash = row["entry_hash"]
            previous_ts = ts

    def query(
        self,
        *,
        event_type: str | None = None,
        actor: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        contains: str | None = None,
    ) -> list[AuditEntry]:
        entries = [self._row_to_entry(e) for e in self._load_entries()]
        from_dt = self._parse_timestamp(from_timestamp) if from_timestamp else None
        to_dt = self._parse_timestamp(to_timestamp) if to_timestamp else None

        result: list[AuditEntry] = []
        for entry in entries:
            if event_type and entry.event_type != event_type:
                continue
            if actor and entry.actor != actor:
                continue

            entry_dt = self._parse_timestamp(entry.timestamp)
            if from_dt and entry_dt < from_dt:
                continue
            if to_dt and entry_dt > to_dt:
                continue
            if contains:
                haystack = json.dumps(entry.details, sort_keys=True)
                if contains not in haystack:
                    continue
            result.append(entry)
        return result

    def _load_entries(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return rows

    def _sign(self, digest: str) -> str:
        sig = hmac.new(self._signing_key, digest.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(sig).decode("ascii")

    @staticmethod
    def _canonical_json(value: dict[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _row_to_entry(row: dict[str, Any]) -> AuditEntry:
        return AuditEntry(
            index=row["index"],
            timestamp=row["timestamp"],
            event_type=row["event_type"],
            actor=row["actor"],
            details=row["details"],
            previous_hash=row["previous_hash"],
            entry_hash=row["entry_hash"],
            signature=row["signature"],
        )
