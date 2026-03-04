"""Performance metrics aggregation for adaptive strategy selection."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class StrategyMetrics:
    """Aggregated metrics used to evaluate a strategy."""

    strategy_id: str
    runs: int
    success_rate: float
    cost_efficiency: float
    latency: float
    error_rate: float
    tool_usage: dict[str, int]


class PerformanceMetrics:
    """Tracks execution outcomes and computes per-strategy metrics."""

    def __init__(self) -> None:
        self._strategy_runs: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def record_execution(
        self,
        *,
        strategy_id: str,
        success: bool,
        latency: float,
        cost: float,
        tools: list[str] | tuple[str, ...] | None = None,
        error: str | None = None,
    ) -> None:
        self._strategy_runs[strategy_id].append(
            {
                "success": bool(success),
                "latency": max(0.0, float(latency)),
                "cost": max(0.0, float(cost)),
                "tools": list(tools or []),
                "error": error,
            }
        )

    def metrics_for_strategy(self, strategy_id: str) -> StrategyMetrics:
        runs = self._strategy_runs.get(strategy_id, [])
        count = len(runs)
        if count == 0:
            return StrategyMetrics(
                strategy_id=strategy_id,
                runs=0,
                success_rate=0.0,
                cost_efficiency=0.0,
                latency=0.0,
                error_rate=0.0,
                tool_usage={},
            )

        successes = sum(1 for item in runs if item["success"])
        total_cost = sum(item["cost"] for item in runs)
        avg_cost = total_cost / count
        avg_latency = sum(item["latency"] for item in runs) / count
        errors = sum(1 for item in runs if item["error"])

        tool_usage: dict[str, int] = defaultdict(int)
        for item in runs:
            for tool in item["tools"]:
                tool_usage[tool] += 1

        # Higher is better. Bounded (0, 1] when avg_cost >= 0.
        cost_efficiency = 1.0 / (1.0 + avg_cost)

        return StrategyMetrics(
            strategy_id=strategy_id,
            runs=count,
            success_rate=successes / count,
            cost_efficiency=cost_efficiency,
            latency=avg_latency,
            error_rate=errors / count,
            tool_usage=dict(tool_usage),
        )

    def all_metrics(self) -> dict[str, StrategyMetrics]:
        return {strategy_id: self.metrics_for_strategy(strategy_id) for strategy_id in self._strategy_runs}
