"""System health service and API router."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

from fastapi import APIRouter


@dataclass(slots=True)
class HealthSnapshot:
    agents_active: int = 0
    queue_depth: int = 0
    worker_utilization: float = 0.0
    task_success_rate: float = 1.0
    error_rate: float = 0.0
    llm_token_consumption: int = 0
    memory_usage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agents_active": self.agents_active,
            "queue_depth": self.queue_depth,
            "worker_utilization": round(self.worker_utilization, 4),
            "task_success_rate": round(self.task_success_rate, 4),
            "error_rate": round(self.error_rate, 4),
            "llm_token_consumption": self.llm_token_consumption,
            "memory_usage": round(self.memory_usage, 4),
        }


class SystemHealthService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._snapshot = HealthSnapshot()

    def update_metrics(self, **metrics: Any) -> HealthSnapshot:
        with self._lock:
            for key, value in metrics.items():
                if hasattr(self._snapshot, key):
                    setattr(self._snapshot, key, value)
            return self.snapshot()

    def snapshot(self) -> HealthSnapshot:
        with self._lock:
            return HealthSnapshot(
                agents_active=self._snapshot.agents_active,
                queue_depth=self._snapshot.queue_depth,
                worker_utilization=self._snapshot.worker_utilization,
                task_success_rate=self._snapshot.task_success_rate,
                error_rate=self._snapshot.error_rate,
                llm_token_consumption=self._snapshot.llm_token_consumption,
                memory_usage=self._snapshot.memory_usage,
            )


health_service = SystemHealthService()
router = APIRouter(tags=["System Health"])


@router.get("/system/health")
async def get_system_health() -> dict[str, Any]:
    return health_service.snapshot().to_dict()
