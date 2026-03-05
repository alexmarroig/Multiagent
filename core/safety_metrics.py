"""Safety metric aggregation and threshold alerting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SafetyMetricThresholds:
    agent_spawn_rate: float = 200.0
    planning_loop_depth: float = 20.0
    queue_growth_rate: float = 100.0
    token_consumption_rate: float = 300.0


class SafetyMetrics:
    """Holds current system safety metrics and emits threshold alerts."""

    def __init__(self, thresholds: SafetyMetricThresholds | None = None) -> None:
        self.thresholds = thresholds or SafetyMetricThresholds()
        self.values = {
            "agent_spawn_rate": 0.0,
            "planning_loop_depth": 0.0,
            "queue_growth_rate": 0.0,
            "token_consumption_rate": 0.0,
        }

    def update(self, **metrics: float) -> None:
        for key, value in metrics.items():
            if key in self.values:
                self.values[key] = float(value)

    def alerts(self) -> list[str]:
        triggered: list[str] = []
        for metric_name, value in self.values.items():
            threshold = getattr(self.thresholds, metric_name)
            if value > threshold:
                triggered.append(f"{metric_name}: {value:.2f} > {threshold:.2f}")
        return triggered
