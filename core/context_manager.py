"""Context preparation utilities for bounded LLM calls."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from memory.vector_memory import MemoryRecord, VectorMemory


@dataclass(slots=True)
class ContextWindowConfig:
    """Defines how much context can be sent to an LLM request."""

    max_context_tokens: int
    reserved_response_tokens: int = 1024

    @property
    def prompt_budget_tokens(self) -> int:
        budget = self.max_context_tokens - self.reserved_response_tokens
        return max(256, budget)


class LLMContextManager:
    """Builds context that fits model limits with retrieval, summarization and prioritization."""

    _KIND_PRIORITY = {
        "goal": 1.0,
        "task_outcome": 0.95,
        "success_metrics": 0.85,
        "evaluation": 0.8,
        "execution_trace": 0.7,
        "task_result": 0.65,
        "knowledge": 0.6,
        "environment_state": 0.4,
        "chunk": 0.35,
        "summary": 0.78,
    }

    def __init__(self, *, memory: VectorMemory, config: ContextWindowConfig) -> None:
        self.memory = memory
        self.config = config

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    @staticmethod
    def _record_text(record: MemoryRecord) -> str:
        return f"{record.kind}: {record.payload}"

    @staticmethod
    def _chunk_text(text: str, *, max_tokens: int) -> list[str]:
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        current: list[str] = []
        current_tokens = 0
        for word in words:
            word_tokens = max(1, math.ceil(len(word) / 4))
            if current and current_tokens + word_tokens > max_tokens:
                chunks.append(" ".join(current))
                current = [word]
                current_tokens = word_tokens
                continue
            current.append(word)
            current_tokens += word_tokens

        if current:
            chunks.append(" ".join(current))

        return chunks

    @classmethod
    def _summarize_records(cls, records: list[MemoryRecord], *, max_tokens: int) -> MemoryRecord | None:
        if not records:
            return None

        snippets: list[str] = []
        consumed = 0
        for record in records:
            text = cls._record_text(record)
            remaining = max_tokens - consumed
            if remaining <= 0:
                break
            max_chars = max(32, remaining * 4)
            shortened = text[:max_chars]
            tokens = cls._estimate_tokens(shortened)
            if consumed + tokens > max_tokens:
                break
            snippets.append(shortened)
            consumed += tokens

        if not snippets:
            return None

        summary_text = " | ".join(snippets)
        return MemoryRecord(
            kind="summary",
            payload={
                "items": len(snippets),
                "summary": summary_text,
                "source_kinds": sorted({record.kind for record in records}),
            },
            embedding=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def _priority_for(cls, record: MemoryRecord) -> float:
        base = cls._KIND_PRIORITY.get(record.kind, 0.5)
        recency_bonus = 0.05 if record.timestamp else 0.0
        return base + recency_bonus

    def _truncate_by_priority(self, records: list[MemoryRecord]) -> list[MemoryRecord]:
        budget = self.config.prompt_budget_tokens
        used = 0
        selected: list[MemoryRecord] = []

        ranked = sorted(records, key=self._priority_for, reverse=True)
        for record in ranked:
            text_tokens = self._estimate_tokens(self._record_text(record))
            if used + text_tokens > budget:
                continue
            selected.append(record)
            used += text_tokens

        return selected

    def _chunk_large_goal_text(self, goals: list[str]) -> list[MemoryRecord]:
        if not goals:
            return []

        goal_text = "\n".join(goals)
        per_chunk_budget = max(64, self.config.prompt_budget_tokens // 5)
        chunks = self._chunk_text(goal_text, max_tokens=per_chunk_budget)

        chunk_records: list[MemoryRecord] = []
        for index, chunk in enumerate(chunks):
            chunk_records.append(
                MemoryRecord(
                    kind="goal" if index == 0 else "chunk",
                    payload={"chunk_index": index, "text": chunk},
                    embedding=[],
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        return chunk_records

    def prepare_planner_context(
        self,
        *,
        goals: list[str],
        extra_records: list[MemoryRecord] | None = None,
    ) -> list[MemoryRecord]:
        query = " ".join(goals) or "active goals"
        dynamic_limit = max(4, min(40, self.config.prompt_budget_tokens // 120))
        retrieved = self.memory.semantic_retrieve(query, limit=dynamic_limit)

        all_records = self._chunk_large_goal_text(goals) + retrieved
        if extra_records:
            all_records.extend(extra_records)

        long_records: list[MemoryRecord] = []
        compact_records: list[MemoryRecord] = []
        long_threshold = max(120, self.config.prompt_budget_tokens // 3)
        for record in all_records:
            if self._estimate_tokens(self._record_text(record)) > long_threshold:
                long_records.append(record)
            else:
                compact_records.append(record)

        summary_budget = max(96, self.config.prompt_budget_tokens // 4)
        summary = self._summarize_records(long_records, max_tokens=summary_budget)
        if summary is not None:
            compact_records.append(summary)

        return self._truncate_by_priority(compact_records)
