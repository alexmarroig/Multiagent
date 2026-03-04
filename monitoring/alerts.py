"""Alerting utilities for failures, unusual behavior, and policy violations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class Alert:
    category: str
    message: str
    payload: dict[str, Any]


class AlertManager:
    def __init__(self, *, failure_threshold: int = 3, unusual_cost_factor: float = 3.0) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.unusual_cost_factor = max(1.0, unusual_cost_factor)
        self._alerts: list[Alert] = []
        self._recent_results: list[dict[str, Any]] = []

    def _emit(self, category: str, message: str, payload: dict[str, Any]) -> Alert:
        alert = Alert(category=category, message=message, payload=payload)
        self._alerts.append(alert)
        return alert

    def observe_result(self, result: dict[str, Any]) -> list[Alert]:
        self._recent_results.append(result)
        emitted: list[Alert] = []

        recent_failures = [item for item in self._recent_results[-self.failure_threshold :] if not item.get("success", False)]
        if len(recent_failures) >= self.failure_threshold:
            emitted.append(
                self._emit(
                    "failure_threshold",
                    "Task failures exceeded configured threshold.",
                    {"threshold": self.failure_threshold, "failures": len(recent_failures)},
                )
            )

        if len(self._recent_results) >= 3:
            costs = [float(item.get("cost", 0.0)) for item in self._recent_results]
            baseline = (sum(costs[:-1]) / max(1, len(costs) - 1)) if len(costs) > 1 else 0.0
            latest_cost = costs[-1]
            if baseline > 0 and latest_cost > baseline * self.unusual_cost_factor:
                emitted.append(
                    self._emit(
                        "unusual_behavior",
                        "Detected unusual cost spike in agent execution.",
                        {"baseline_cost": baseline, "latest_cost": latest_cost},
                    )
                )

        if violation := result.get("policy_violation"):
            emitted.append(
                self._emit(
                    "policy_violation",
                    "Policy violation reported during execution.",
                    {"violation": violation, "task_id": result.get("task_id")},
                )
            )

        return emitted

    def alerts(self) -> list[Alert]:
        return list(self._alerts)
