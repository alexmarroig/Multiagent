"""Strategy ranking based on adaptive performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .performance_metrics import PerformanceMetrics, StrategyMetrics


@dataclass(slots=True, frozen=True)
class StrategyScore:
    strategy_id: str
    score: float
    success_rate: float
    cost_efficiency: float
    latency: float


class StrategyOptimizer:
    """Scores and prioritizes strategies over time."""

    def __init__(
        self,
        performance_metrics: PerformanceMetrics,
        *,
        success_weight: float = 0.6,
        cost_weight: float = 0.25,
        latency_weight: float = 0.15,
    ) -> None:
        self.performance_metrics = performance_metrics
        self.success_weight = success_weight
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight

    def score_strategy(self, strategy_id: str) -> StrategyScore:
        metrics = self.performance_metrics.metrics_for_strategy(strategy_id)
        score = self._weighted_score(metrics)
        return StrategyScore(
            strategy_id=strategy_id,
            score=score,
            success_rate=metrics.success_rate,
            cost_efficiency=metrics.cost_efficiency,
            latency=metrics.latency,
        )

    def prioritize_strategies(self, strategy_ids: list[str]) -> list[StrategyScore]:
        ranked = [self.score_strategy(strategy_id) for strategy_id in strategy_ids]
        return sorted(ranked, key=lambda item: item.score, reverse=True)

    def _weighted_score(self, metrics: StrategyMetrics) -> float:
        # Convert latency so lower latency increases score.
        latency_component = 1.0 / (1.0 + metrics.latency)
        return (
            (metrics.success_rate * self.success_weight)
            + (metrics.cost_efficiency * self.cost_weight)
            + (latency_component * self.latency_weight)
        )
