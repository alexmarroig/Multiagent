"""Semantic cache for reusing LLM responses for similar prompts."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


def _default_embedding(text: str) -> list[float]:
    """Deterministic lightweight embedding fallback for tests/offline mode."""

    digest = hashlib.sha256(text.strip().lower().encode("utf-8")).digest()
    return [byte / 255.0 for byte in digest[:32]]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


@dataclass(slots=True)
class SemanticCacheEntry:
    prompt: str
    response: str
    embedding: list[float]


class SemanticLLMCache:
    """Stores prompt/response pairs and reuses responses by similarity."""

    def __init__(self, similarity_threshold: float = 0.92, max_entries: int = 2_000) -> None:
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self._entries: list[SemanticCacheEntry] = []

    def lookup(self, prompt: str, embedding: list[float] | None = None) -> str | None:
        vector = embedding or _default_embedding(prompt)
        best_score = 0.0
        best_response: str | None = None

        for entry in self._entries:
            score = _cosine_similarity(vector, entry.embedding)
            if score > best_score:
                best_score = score
                best_response = entry.response

        if best_score >= self.similarity_threshold:
            return best_response
        return None

    def store(self, prompt: str, response: str, embedding: list[float] | None = None) -> None:
        vector = embedding or _default_embedding(prompt)
        self._entries.append(SemanticCacheEntry(prompt=prompt, response=response, embedding=vector))
        if len(self._entries) > self.max_entries:
            self._entries.pop(0)

    def size(self) -> int:
        return len(self._entries)
