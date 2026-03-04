"""Alerting utilities for failures, unusual behavior, and policy violations."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from monitoring.structured_logging import log_event


@dataclass(slots=True, frozen=True)
class Alert:
    category: str
    message: str
    payload: dict[str, Any]


class AlertManager:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        unusual_cost_factor: float = 3.0,
        queue_high_watermark: int = 500,
        error_rate_threshold: float = 0.05,
        repeated_worker_crashes: int = 3,
        llm_budget_limit: float = 100.0,
        webhook_url: str | None = None,
    ) -> None:
        self.failure_threshold = max(1, failure_threshold)
        self.unusual_cost_factor = max(1.0, unusual_cost_factor)
        self.queue_high_watermark = max(1, queue_high_watermark)
        self.error_rate_threshold = max(0.0, error_rate_threshold)
        self.repeated_worker_crashes = max(1, repeated_worker_crashes)
        self.llm_budget_limit = max(0.0, llm_budget_limit)
        self.webhook_url = webhook_url
        self._alerts: list[Alert] = []
        self._recent_results: list[dict[str, Any]] = []
        self._worker_crash_counts: dict[str, int] = {}
        self._logger = logging.getLogger(__name__)

    def _emit(self, category: str, message: str, payload: dict[str, Any]) -> Alert:
        alert = Alert(category=category, message=message, payload=payload)
        self._alerts.append(alert)
        log_event(self._logger, component="alerting", event="alert_triggered", severity="warning", category=category, message=message, payload=payload)
        self._send_webhook(alert)
        self._send_email_stub(alert)
        return alert

    def _send_webhook(self, alert: Alert) -> None:
        if not self.webhook_url:
            return
        log_event(self._logger, component="alerting", event="webhook_dispatched", severity="info", webhook_url=self.webhook_url, category=alert.category)

    def _send_email_stub(self, alert: Alert) -> None:
        log_event(self._logger, component="alerting", event="email_stub", severity="info", category=alert.category, subject=f"Agent Platform Alert: {alert.category}")

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

    def evaluate_runtime_signals(
        self,
        *,
        queue_depth: int,
        error_rate: float,
        worker_id: str | None = None,
        worker_crashed: bool = False,
        llm_cost: float = 0.0,
    ) -> list[Alert]:
        emitted: list[Alert] = []
        if queue_depth > self.queue_high_watermark:
            emitted.append(
                self._emit(
                    "queue_high_watermark",
                    "Queue depth exceeded high watermark.",
                    {"queue_depth": queue_depth, "high_watermark": self.queue_high_watermark},
                )
            )

        if error_rate > self.error_rate_threshold:
            emitted.append(
                self._emit(
                    "error_rate_threshold",
                    "Runtime error rate exceeded threshold.",
                    {"error_rate": error_rate, "threshold": self.error_rate_threshold},
                )
            )

        if worker_crashed and worker_id:
            self._worker_crash_counts[worker_id] = self._worker_crash_counts.get(worker_id, 0) + 1
            if self._worker_crash_counts[worker_id] >= self.repeated_worker_crashes:
                emitted.append(
                    self._emit(
                        "repeated_worker_crashes",
                        "Worker crashed repeatedly.",
                        {"worker_id": worker_id, "crashes": self._worker_crash_counts[worker_id]},
                    )
                )

        if llm_cost > self.llm_budget_limit:
            emitted.append(
                self._emit(
                    "llm_budget_exceeded",
                    "LLM cost exceeded configured budget.",
                    {"llm_cost": llm_cost, "budget": self.llm_budget_limit},
                )
            )

        return emitted

    def alerts(self) -> list[Alert]:
        return list(self._alerts)
