"""Vector-style memory for autonomous agents with semantic retrieval."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class MemoryRecord:
    kind: str
    payload: dict[str, Any]
    embedding: list[float]
    timestamp: str


class VectorMemory:
    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    def _embed(self, text: str, dimensions: int = 32) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(dimensions):
            value = digest[i % len(digest)] / 255.0
            vector.append(value)
        return vector

    def _store(self, kind: str, payload: dict[str, Any]) -> MemoryRecord:
        content = f"{kind}:{payload}"
        record = MemoryRecord(
            kind=kind,
            payload=payload,
            embedding=self._embed(content),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._records.append(record)
        return record

    def store_task_result(self, task_id: str, result: dict[str, Any]) -> MemoryRecord:
        return self._store("task_result", {"task_id": task_id, "result": result})

    def store_agent_decision(self, decision: dict[str, Any]) -> MemoryRecord:
        return self._store("agent_decision", decision)

    def store_knowledge(self, knowledge: dict[str, Any]) -> MemoryRecord:
        return self._store("knowledge", knowledge)

    def store_environment_state(self, state: dict[str, Any]) -> MemoryRecord:
        return self._store("environment_state", state)

    def semantic_retrieve(self, query: str, *, limit: int = 5) -> list[MemoryRecord]:
        if not self._records:
            return []

        q_embedding = self._embed(query)

        def cosine(a: list[float], b: list[float]) -> float:
            numerator = sum(x * y for x, y in zip(a, b, strict=False))
            a_norm = math.sqrt(sum(x * x for x in a))
            b_norm = math.sqrt(sum(y * y for y in b))
            if a_norm == 0 or b_norm == 0:
                return 0.0
            return numerator / (a_norm * b_norm)

        ranked = sorted(self._records, key=lambda r: cosine(q_embedding, r.embedding), reverse=True)
        return ranked[: max(1, limit)]
