"""Transactional persistent store for governance approvals."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ApprovalRecord:
    token: str
    reason: str
    payload: dict[str, Any]
    status: str
    decision: str | None
    decision_by: str | None
    decision_comment: str
    created_at: str
    resolved_at: str | None


class ApprovalStore:
    def __init__(self, db_path: str = "governance_approvals.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS approvals (
                    token TEXT PRIMARY KEY,
                    reason TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decision TEXT,
                    decision_by TEXT,
                    decision_comment TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS approval_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(token) REFERENCES approvals(token)
                )
                """
            )

    def create(self, *, token: str, reason: str, payload: dict[str, Any] | None = None) -> ApprovalRecord:
        now = _now()
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                "INSERT OR IGNORE INTO approvals(token, reason, payload_json, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
                (token, reason, json.dumps(payload or {}), now),
            )
            conn.execute(
                "INSERT INTO approval_history(token, action, actor, details_json, created_at) VALUES (?, 'submitted', 'system', ?, ?)",
                (token, json.dumps({"reason": reason}), now),
            )
            conn.commit()
        return self.get(token)

    def add_history(self, *, token: str, action: str, actor: str, details: dict[str, Any] | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO approval_history(token, action, actor, details_json, created_at) VALUES (?, ?, ?, ?, ?)",
                (token, action, actor, json.dumps(details or {}), _now()),
            )

    def record_decision(self, *, token: str, decision: str, reviewer: str, comment: str = "") -> ApprovalRecord:
        resolved_at = _now()
        with self._connect() as conn:
            conn.execute("BEGIN")
            conn.execute(
                "UPDATE approvals SET status=?, decision=?, decision_by=?, decision_comment=?, resolved_at=? WHERE token=?",
                (decision, decision, reviewer, comment, resolved_at, token),
            )
            conn.execute(
                "INSERT INTO approval_history(token, action, actor, details_json, created_at) VALUES (?, 'decision_recorded', ?, ?, ?)",
                (token, reviewer, json.dumps({"decision": decision, "comment": comment}), resolved_at),
            )
            conn.commit()
        return self.get(token)

    def get(self, token: str) -> ApprovalRecord:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM approvals WHERE token=?", (token,)).fetchone()
        if row is None:
            raise KeyError(token)
        return ApprovalRecord(
            token=row["token"],
            reason=row["reason"],
            payload=json.loads(row["payload_json"]),
            status=row["status"],
            decision=row["decision"],
            decision_by=row["decision_by"],
            decision_comment=row["decision_comment"],
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
        )

    def pending(self) -> list[ApprovalRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM approvals WHERE status='pending'").fetchall()
        return [self.get(row["token"]) for row in rows]

    def history(self, token: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT action, actor, details_json, created_at FROM approval_history WHERE token=? ORDER BY id", (token,)).fetchall()
        return [{"action": r["action"], "actor": r["actor"], "details": json.loads(r["details_json"]), "created_at": r["created_at"]} for r in rows]
