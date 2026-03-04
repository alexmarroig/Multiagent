"""Performance feedback and failure-pattern tracking for planner adaptation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class PerformanceSnapshot:
    success_rate: float
    average_execution_time: float
    average_cost: float
    repeated_failures: bool


class PerformanceFeedback:
    """Aggregates execution results and computes planning signals."""

    def __init__(self, *, failure_window: int = 5, failure_threshold: int = 3) -> None:
        self.failure_window = max(1, failure_window)
        self.failure_threshold = max(1, failure_threshold)
        self._task_results: list[dict[str, Any]] = []
        self._agent_stats: dict[str, dict[str, float]] = defaultdict(
            lambda: {"runs": 0.0, "success": 0.0, "total_time": 0.0, "total_cost": 0.0}
        )
        self._tool_stats: dict[str, dict[str, float]] = defaultdict(lambda: {"runs": 0.0, "success": 0.0})
        self._failures = deque(maxlen=self.failure_window)

    def evaluate_task_success(self, result: dict[str, Any]) -> bool:
        if "success" in result:
            return bool(result["success"])
        if "status" in result:
            return str(result["status"]).lower() in {"ok", "done", "success", "completed"}
        return not bool(result.get("error"))

    def record_execution(self, result: dict[str, Any]) -> bool:
        success = self.evaluate_task_success(result)
        execution_time = float(result.get("execution_time", 0.0))
        cost = float(result.get("cost", 0.0))
        agent_id = str(result.get("agent_id", "unknown"))
        tool_id = str(result.get("tool", result.get("tool_id", "unknown")))

        self._task_results.append(
            {
                "success": success,
                "execution_time": execution_time,
                "cost": cost,
                "agent_id": agent_id,
                "tool_id": tool_id,
                "task_id": result.get("task_id"),
            }
        )

        agent = self._agent_stats[agent_id]
        agent["runs"] += 1
        agent["success"] += 1 if success else 0
        agent["total_time"] += execution_time
        agent["total_cost"] += cost

        tool = self._tool_stats[tool_id]
        tool["runs"] += 1
        tool["success"] += 1 if success else 0

        self._failures.append(0 if success else 1)
        return success

    def detect_repeated_failures(self) -> bool:
        return sum(self._failures) >= self.failure_threshold

    def planner_signals(self) -> dict[str, Any]:
        runs = len(self._task_results)
        successes = sum(1 for item in self._task_results if item["success"])
        avg_time = sum(item["execution_time"] for item in self._task_results) / runs if runs else 0.0
        avg_cost = sum(item["cost"] for item in self._task_results) / runs if runs else 0.0

        return {
            "global_success_rate": (successes / runs) if runs else 0.0,
            "average_execution_time": avg_time,
            "average_cost": avg_cost,
            "repeated_failures": self.detect_repeated_failures(),
            "agent_performance": {
                agent_id: {
                    "success_rate": (stats["success"] / stats["runs"]) if stats["runs"] else 0.0,
                    "avg_execution_time": (stats["total_time"] / stats["runs"]) if stats["runs"] else 0.0,
                    "avg_cost": (stats["total_cost"] / stats["runs"]) if stats["runs"] else 0.0,
                }
                for agent_id, stats in self._agent_stats.items()
            },
            "tool_effectiveness": {
                tool_id: (stats["success"] / stats["runs"]) if stats["runs"] else 0.0
                for tool_id, stats in self._tool_stats.items()
            },
        }

    def snapshot(self) -> PerformanceSnapshot:
        signals = self.planner_signals()
        return PerformanceSnapshot(
            success_rate=float(signals["global_success_rate"]),
            average_execution_time=float(signals["average_execution_time"]),
            average_cost=float(signals["average_cost"]),
            repeated_failures=bool(signals["repeated_failures"]),
        )
