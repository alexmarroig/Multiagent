"""Rolling-window anomaly detection for runtime health signals."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import sqrt


@dataclass(slots=True, frozen=True)
class Anomaly:
    metric: str
    value: float
    baseline_mean: float
    baseline_stddev: float
    z_score: float


class RollingAnomalyDetector:
    def __init__(self, *, window_size: int = 30, min_samples: int = 6, z_score_threshold: float = 2.5) -> None:
        self.window_size = max(3, window_size)
        self.min_samples = max(3, min_samples)
        self.z_score_threshold = max(1.0, z_score_threshold)
        self._series: dict[str, deque[float]] = {
            "error_rate": deque(maxlen=self.window_size),
            "queue_depth": deque(maxlen=self.window_size),
            "task_latency": deque(maxlen=self.window_size),
            "agent_crash_frequency": deque(maxlen=self.window_size),
        }

    @staticmethod
    def _mean(values: list[float]) -> float:
        return sum(values) / len(values)

    @staticmethod
    def _stddev(values: list[float], baseline_mean: float) -> float:
        if len(values) < 2:
            return 0.0
        variance = sum((value - baseline_mean) ** 2 for value in values) / len(values)
        return sqrt(variance)

    def _detect_metric_anomaly(self, metric: str, value: float) -> Anomaly | None:
        history = self._series[metric]
        if len(history) < self.min_samples:
            history.append(value)
            return None

        baseline = list(history)
        baseline_mean = self._mean(baseline)
        baseline_stddev = self._stddev(baseline, baseline_mean)

        history.append(value)

        if baseline_stddev <= 0:
            return None

        z_score = (value - baseline_mean) / baseline_stddev
        if z_score < self.z_score_threshold:
            return None

        return Anomaly(
            metric=metric,
            value=value,
            baseline_mean=baseline_mean,
            baseline_stddev=baseline_stddev,
            z_score=z_score,
        )

    def detect_runtime_anomalies(
        self,
        *,
        error_rate: float,
        queue_depth: int,
        task_latency: float,
        worker_crashed: bool,
    ) -> list[Anomaly]:
        points: dict[str, float] = {
            "error_rate": float(error_rate),
            "queue_depth": float(queue_depth),
            "task_latency": float(task_latency),
            "agent_crash_frequency": 1.0 if worker_crashed else 0.0,
        }

        anomalies: list[Anomaly] = []
        for metric, value in points.items():
            anomaly = self._detect_metric_anomaly(metric, value)
            if anomaly is not None:
                anomalies.append(anomaly)
        return anomalies
