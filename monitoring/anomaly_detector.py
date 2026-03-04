"""Simple anomaly detector for runtime metric streams."""

from __future__ import annotations

from statistics import mean


class AnomalyDetector:
    def detect_cost_spike(self, historical: list[float], latest: float, multiplier: float = 2.0) -> bool:
        if len(historical) < 3:
            return False
        baseline = mean(historical)
        return baseline > 0 and latest > baseline * multiplier

    def detect_error_spike(self, historical_rates: list[float], latest: float, threshold: float = 0.15) -> bool:
        if len(historical_rates) < 3:
            return latest > threshold
        return latest > max(threshold, mean(historical_rates) * 1.5)
