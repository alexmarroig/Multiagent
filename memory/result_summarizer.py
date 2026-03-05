"""Result summarization and context compression helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SummarizationConfig:
    max_chars: int = 600
    max_items: int = 20


class ResultSummarizer:
    def __init__(self, config: SummarizationConfig | None = None) -> None:
        self.config = config or SummarizationConfig()

    def llm_summarize(self, outputs: list[dict[str, Any]]) -> str:
        slices = [str(item.get("output", ""))[:120] for item in outputs[: self.config.max_items]]
        joined = " | ".join(slices)
        return joined[: self.config.max_chars]

    def embedding_compress(self, embedding: list[float], target_dimensions: int = 128) -> list[float]:
        if target_dimensions <= 0:
            raise ValueError("target_dimensions must be positive")
        if len(embedding) <= target_dimensions:
            return embedding
        stride = max(1, len(embedding) // target_dimensions)
        compressed = [embedding[i] for i in range(0, len(embedding), stride)]
        return compressed[:target_dimensions]

    def trim_context(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return history[-self.config.max_items :]
