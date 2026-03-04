"""Vector-style memory for autonomous agents with semantic retrieval."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from monitoring.tracing import get_tracer


@dataclass(slots=True)
class MemoryRecord:
    kind: str
    payload: dict[str, Any]
    embedding: list[float]
    timestamp: str


class VectorMemory:
    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []
        self._tracer = get_tracer()

    def _embed(self, text: str, dimensions: int = 32) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(dimensions):
            value = digest[i % len(digest)] / 255.0
            vector.append(value)
        return vector

    def _store(self, kind: str, payload: dict[str, Any]) -> MemoryRecord:
        with self._tracer.start_span("memory.store", kind="memory_access", attributes={"memory_kind": kind}):
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
        with self._tracer.start_span("memory.retrieve", kind="memory_access", attributes={"limit": limit}):
            if not self._records:
                return []
            q_embedding = self._embed(query)

            def is_valid_record(record: object) -> bool:
                if not isinstance(record, MemoryRecord):
                    return False
                if not isinstance(record.payload, dict):
                    return False
                if not isinstance(record.embedding, list):
                    return False
                return all(isinstance(value, int | float) for value in record.embedding)

            def cosine(a: list[float], b: list[float]) -> float:
                numerator = sum(x * y for x, y in zip(a, b, strict=False))
                a_norm = math.sqrt(sum(x * x for x in a))
                b_norm = math.sqrt(sum(y * y for y in b))
                if a_norm == 0 or b_norm == 0:
                    return 0.0
                return numerator / (a_norm * b_norm)

            valid_records = [record for record in self._records if is_valid_record(record)]
            if not valid_records:
                return []
            ranked = sorted(valid_records, key=lambda r: cosine(q_embedding, r.embedding), reverse=True)
            return ranked[: max(1, limit)]
