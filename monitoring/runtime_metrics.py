"""In-memory runtime metrics registry for enterprise controls and observability."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock


class RuntimeMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._histograms: dict[str, list[float]] = defaultdict(list)

    def inc(self, name: str, amount: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += amount

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self._histograms[name].append(float(value))

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            histogram_avg = {
                f"{name}_avg": (sum(values) / len(values) if values else 0.0)
                for name, values in self._histograms.items()
            }
            histogram_count = {f"{name}_count": float(len(values)) for name, values in self._histograms.items()}
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {**histogram_avg, **histogram_count},
            }

    def to_prometheus(self) -> str:
        snapshot = self.snapshot()
        lines: list[str] = []
        for metric_type, values in snapshot.items():
            for name, value in sorted(values.items()):
                sanitized = name.replace(".", "_").replace("-", "_")
                lines.append(f"# TYPE {sanitized} {'gauge' if metric_type != 'counters' else 'counter'}")
                lines.append(f"{sanitized} {value}")
        return "\n".join(lines) + "\n"


runtime_metrics = RuntimeMetrics()
