"""Model pooling with request batching and task-complexity based routing."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Any


class ModelTier(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    HIGH_REASONING = "high_reasoning"


@dataclass(slots=True)
class ModelRequest:
    request_id: str
    prompt: str
    complexity: float = 0.5
    metadata: dict[str, Any] | None = None


class ModelPool:
    """Maintains per-tier pools, batches requests, and routes to fit-for-purpose models."""

    def __init__(self, pool_size_per_tier: int = 16) -> None:
        self.pool_size_per_tier = max(1, pool_size_per_tier)
        self._connections: dict[ModelTier, deque[str]] = {
            tier: deque(f"{tier.value}-conn-{i:03d}" for i in range(self.pool_size_per_tier)) for tier in ModelTier
        }
        self._pending: dict[ModelTier, list[ModelRequest]] = defaultdict(list)
        self._lock = Lock()

    def route(self, request: ModelRequest) -> ModelTier:
        if request.complexity >= 0.8:
            return ModelTier.HIGH_REASONING
        if request.complexity <= 0.3:
            return ModelTier.FAST
        return ModelTier.BALANCED

    def submit(self, request: ModelRequest) -> ModelTier:
        tier = self.route(request)
        with self._lock:
            self._pending[tier].append(request)
        return tier

    def flush_batch(self, tier: ModelTier) -> list[dict[str, Any]]:
        with self._lock:
            requests = self._pending[tier]
            self._pending[tier] = []
        if not requests:
            return []
        connection_id = self._acquire_connection(tier)
        try:
            return [
                {
                    "request_id": request.request_id,
                    "tier": tier.value,
                    "connection": connection_id,
                    "result": f"processed:{request.prompt[:64]}",
                }
                for request in requests
            ]
        finally:
            self._release_connection(tier, connection_id)

    def _acquire_connection(self, tier: ModelTier) -> str:
        pool = self._connections[tier]
        if not pool:
            return f"{tier.value}-overflow"
        conn = pool.popleft()
        return conn

    def _release_connection(self, tier: ModelTier, connection_id: str) -> None:
        if connection_id.endswith("overflow"):
            return
        self._connections[tier].append(connection_id)
