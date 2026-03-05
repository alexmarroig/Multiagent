"""Memory retention and quota governance with TTL and compaction."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class MemoryGovernancePolicy:
    tenant_max_records: int = 20_000
    record_ttl_seconds: int = 60 * 60 * 24 * 30
    max_vector_dimensions: int = 512


class MemoryGovernor:
    def __init__(self, db_path: str = "agentos_memory.db", *, policies: dict[str, MemoryGovernancePolicy] | None = None) -> None:
        self.db_path = Path(db_path)
        self.policies = policies or {}
        self.default_policy = MemoryGovernancePolicy()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def policy_for(self, tenant_id: str) -> MemoryGovernancePolicy:
        return self.policies.get(tenant_id, self.default_policy)

    def compact(self, tenant_id: str) -> dict[str, int]:
        policy = self.policy_for(tenant_id)
        cutoff = time.time() - policy.record_ttl_seconds
        with self._conn() as conn:
            deleted_ttl = conn.execute(
                "DELETE FROM task_history WHERE namespace LIKE ? AND created_at < ?",
                (f"tenant:{tenant_id}:%", cutoff),
            ).rowcount

            count_row = conn.execute(
                "SELECT COUNT(*) AS n FROM task_history WHERE namespace LIKE ?",
                (f"tenant:{tenant_id}:%",),
            ).fetchone()
            current_count = int(count_row["n"] if count_row else 0)
            over = max(0, current_count - policy.tenant_max_records)
            deleted_quota = 0
            if over:
                deleted_quota = conn.execute(
                    """
                    DELETE FROM task_history
                    WHERE key IN (
                        SELECT key FROM task_history
                        WHERE namespace LIKE ?
                        ORDER BY created_at ASC
                        LIMIT ?
                    )
                    """,
                    (f"tenant:{tenant_id}:%", over),
                ).rowcount
            conn.commit()
        return {"deleted_ttl": deleted_ttl, "deleted_quota": deleted_quota}

    def prune_vector(self, embedding: list[float], tenant_id: str) -> list[float]:
        max_dims = self.policy_for(tenant_id).max_vector_dimensions
        return embedding[:max_dims] if len(embedding) > max_dims else embedding
