"""Store simples de métricas operacionais para backend/orquestrador."""

from __future__ import annotations

from collections import defaultdict, deque
from statistics import quantiles
from threading import Lock
from time import monotonic
from typing import Any


class MetricsStore:
    """Mantém métricas in-memory para dashboards e health operacional."""

    def __init__(self, max_samples: int = 2000):
        self._lock = Lock()
        self._task_latencies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=max_samples))
        self._run_durations: deque[float] = deque(maxlen=max_samples)
        self._run_started_at: dict[str, float] = {}
        self._run_status: dict[str, str] = {}
        self._tool_calls: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "errors": 0})
        self._external_tool_calls: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "errors": 0}
        )
        self._websocket_failures = 0

    def mark_run_started(self, session_id: str) -> None:
        with self._lock:
            self._run_started_at[session_id] = monotonic()
            self._run_status[session_id] = "running"

    def mark_run_finished(self, session_id: str, status: str) -> None:
        with self._lock:
            started = self._run_started_at.pop(session_id, None)
            self._run_status[session_id] = status
            if started is not None:
                self._run_durations.append(monotonic() - started)

    def record_task_latency(self, task_id: str, latency_seconds: float) -> None:
        with self._lock:
            self._task_latencies[task_id].append(latency_seconds)

    def record_tool_call(self, tool_id: str, success: bool, external: bool = False) -> None:
        with self._lock:
            bucket = self._external_tool_calls if external else self._tool_calls
            bucket[tool_id]["total"] += 1
            if not success:
                bucket[tool_id]["errors"] += 1

    def record_websocket_failure(self) -> None:
        with self._lock:
            self._websocket_failures += 1

    @staticmethod
    def _rate(data: dict[str, int]) -> float:
        total = data["total"]
        if total == 0:
            return 0.0
        return round(data["errors"] / total, 4)

    @staticmethod
    def _p95(values: list[float]) -> float:
        if not values:
            return 0.0
        if len(values) < 2:
            return round(values[0], 4)
        return round(quantiles(values, n=100, method="inclusive")[94], 4)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            task_snapshot = {
                task_id: {
                    "samples": len(latencies),
                    "avg_seconds": round(sum(latencies) / len(latencies), 4) if latencies else 0.0,
                    "p95_seconds": self._p95(list(latencies)),
                }
                for task_id, latencies in self._task_latencies.items()
            }

            tool_snapshot = {
                tool_id: {
                    "total": stats["total"],
                    "errors": stats["errors"],
                    "error_rate": self._rate(stats),
                }
                for tool_id, stats in self._tool_calls.items()
            }
            external_tool_snapshot = {
                tool_id: {
                    "total": stats["total"],
                    "errors": stats["errors"],
                    "error_rate": self._rate(stats),
                }
                for tool_id, stats in self._external_tool_calls.items()
            }
            run_durations = list(self._run_durations)
            backlog = sum(1 for status in self._run_status.values() if status == "running")

            return {
                "runs": {
                    "samples": len(run_durations),
                    "total_time_avg_seconds": round(sum(run_durations) / len(run_durations), 4)
                    if run_durations
                    else 0.0,
                    "total_time_p95_seconds": self._p95(run_durations),
                    "backlog_running": backlog,
                },
                "tasks": task_snapshot,
                "tools": tool_snapshot,
                "external_integrations": external_tool_snapshot,
                "websocket": {"failures": self._websocket_failures},
            }


metrics_store = MetricsStore()
