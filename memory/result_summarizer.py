"""Result summarization and context compression helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model_gateway import ModelGateway, ModelRequest
from security.tenant_context import TenantContext


@dataclass(slots=True)
class SummarizationConfig:
    max_chars: int = 600
    max_items: int = 20


class ResultSummarizer:
    def __init__(self, config: SummarizationConfig | None = None, *, model_gateway: ModelGateway | None = None) -> None:
        self.config = config or SummarizationConfig()
        self.model_gateway = model_gateway

    def llm_summarize(self, outputs: list[dict[str, Any]], *, context: TenantContext | None = None) -> str:
        slices = [str(item.get("output", ""))[:120] for item in outputs[: self.config.max_items]]
        joined = " | ".join(slices)
        if self.model_gateway is None or context is None:
            return joined[: self.config.max_chars]
        response = self.model_gateway.call(
            ModelRequest(
                prompt=f"Summarize: {joined}",
                model="summary-default",
                max_tokens=256,
                estimated_tokens=min(512, max(1, len(joined) // 3)),
                estimated_cost=0.001 * max(1, len(joined) // 100),
                metadata={"operation": "result_summarization"},
            ),
            context=context,
        )
        return str(response["output"])[: self.config.max_chars]

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
