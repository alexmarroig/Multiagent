"""Distributed memory layer combining relational history with vector search semantics."""

from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MemoryEntry:
    key: str
    value: dict[str, Any]
    embedding: list[float] = field(default_factory=list)
    namespace: str = "global"
    created_at: float = field(default_factory=time.time)


class DistributedMemory:
    """Persists task history/state in SQL and supports semantic retrieval via vector similarity."""

    def __init__(self, db_path: str = "agentos_memory.db") -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._bootstrap()

    def _bootstrap(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_history (
                key TEXT PRIMARY KEY,
                namespace TEXT NOT NULL,
                value_json TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS world_model (
                key TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def store_task_history(self, entry: MemoryEntry) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO task_history (key, namespace, value_json, embedding_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.key,
                entry.namespace,
                json.dumps(entry.value),
                json.dumps(entry.embedding),
                entry.created_at,
            ),
        )
        self._conn.commit()

    def semantic_vector_search(self, query_embedding: list[float], *, limit: int = 5, namespace: str | None = None) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT key, namespace, value_json, embedding_json, created_at FROM task_history"
            + (" WHERE namespace = ?" if namespace else ""),
            ((namespace,) if namespace else ()),
        ).fetchall()

        def cosine(a: list[float], b: list[float]) -> float:
            if not a or not b or len(a) != len(b):
                return -1.0
            dot = sum(x * y for x, y in zip(a, b))
            a_norm = math.sqrt(sum(x * x for x in a))
            b_norm = math.sqrt(sum(y * y for y in b))
            if a_norm == 0 or b_norm == 0:
                return -1.0
            return dot / (a_norm * b_norm)

        ranked = sorted(
            (
                {
                    "key": row["key"],
                    "namespace": row["namespace"],
                    "value": json.loads(row["value_json"]),
                    "score": cosine(query_embedding, json.loads(row["embedding_json"])),
                    "created_at": row["created_at"],
                }
                for row in rows
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        return ranked[: max(1, limit)]

    def save_agent_state(self, agent_id: str, state: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO agent_state (agent_id, state_json, updated_at) VALUES (?, ?, ?)",
            (agent_id, json.dumps(state), time.time()),
        )
        self._conn.commit()

    def load_agent_state(self, agent_id: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT state_json FROM agent_state WHERE agent_id = ?", (agent_id,)).fetchone()
        if not row:
            return None
        return json.loads(row["state_json"])

    def update_shared_world_model(self, key: str, data: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO world_model (key, data_json, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(data), time.time()),
        )
        self._conn.commit()

    def get_shared_world_model(self, key: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT data_json FROM world_model WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return json.loads(row["data_json"])
