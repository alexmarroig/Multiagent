"""SLO monitoring for reliability signals and automated mitigation triggers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable
from uuid import uuid4


@dataclass(slots=True)
class SLOThresholds:
    """Thresholds that define SLO compliance."""

    task_success_rate_min: float = 0.99
    task_latency_max_seconds: float = 2.0
    queue_delay_max_seconds: float = 1.0
    worker_uptime_min: float = 0.995


@dataclass(slots=True, frozen=True)
class SLOSnapshot:
    """Current values of the SLO-relevant metrics."""

    task_success_rate: float
    task_latency_seconds: float
    queue_delay_seconds: float
    worker_uptime: float


@dataclass(slots=True, frozen=True)
class SLOAlert:
    """Alert produced when an SLO is violated."""

    category: str
    message: str
    payload: dict[str, Any]


@dataclass(slots=True, frozen=True)
class SLOIncident:
    """Incident record for an SLO violation."""

    incident_id: str
    metric: str
    message: str
    observed_value: float
    threshold_value: float
    threshold_condition: str
    created_at: str
    mitigation_triggered: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class SLOMonitor:
    """Tracks SLO metrics and reacts to threshold violations."""

    def __init__(
        self,
        thresholds: SLOThresholds | None = None,
        *,
        alert_emitter: Callable[[SLOAlert], None] | None = None,
        incident_recorder: Callable[[SLOIncident], None] | None = None,
        mitigation_workflow: Callable[[SLOIncident], None] | None = None,
    ) -> None:
        self._thresholds = thresholds or SLOThresholds()
        self._alert_emitter = alert_emitter
        self._incident_recorder = incident_recorder
        self._mitigation_workflow = mitigation_workflow
        self._lock = Lock()
        self._alerts: list[SLOAlert] = []
        self._incidents: list[SLOIncident] = []

    def update_thresholds(self, **updates: float) -> SLOThresholds:
        with self._lock:
            for key, value in updates.items():
                if hasattr(self._thresholds, key):
                    setattr(self._thresholds, key, float(value))
            return self.thresholds()

    def thresholds(self) -> SLOThresholds:
        with self._lock:
            return SLOThresholds(
                task_success_rate_min=self._thresholds.task_success_rate_min,
                task_latency_max_seconds=self._thresholds.task_latency_max_seconds,
                queue_delay_max_seconds=self._thresholds.queue_delay_max_seconds,
                worker_uptime_min=self._thresholds.worker_uptime_min,
            )

    def evaluate(self, snapshot: SLOSnapshot) -> list[SLOIncident]:
        """Evaluate a new metric snapshot and react to SLO violations."""

        checks = [
            (
                "task_success_rate",
                snapshot.task_success_rate,
                self._thresholds.task_success_rate_min,
                "below_minimum",
                snapshot.task_success_rate < self._thresholds.task_success_rate_min,
            ),
            (
                "task_latency_seconds",
                snapshot.task_latency_seconds,
                self._thresholds.task_latency_max_seconds,
                "above_maximum",
                snapshot.task_latency_seconds > self._thresholds.task_latency_max_seconds,
            ),
            (
                "queue_delay_seconds",
                snapshot.queue_delay_seconds,
                self._thresholds.queue_delay_max_seconds,
                "above_maximum",
                snapshot.queue_delay_seconds > self._thresholds.queue_delay_max_seconds,
            ),
            (
                "worker_uptime",
                snapshot.worker_uptime,
                self._thresholds.worker_uptime_min,
                "below_minimum",
                snapshot.worker_uptime < self._thresholds.worker_uptime_min,
            ),
        ]

        emitted: list[SLOIncident] = []
        for metric, observed, threshold, condition, violated in checks:
            if not violated:
                continue
            emitted.append(
                self._handle_violation(
                    metric=metric,
                    observed_value=observed,
                    threshold_value=threshold,
                    threshold_condition=condition,
                )
            )
        return emitted

    def _handle_violation(
        self,
        *,
        metric: str,
        observed_value: float,
        threshold_value: float,
        threshold_condition: str,
    ) -> SLOIncident:
        message = f"SLO violation detected for {metric}: observed={observed_value:.4f}, threshold={threshold_value:.4f}."
        incident = SLOIncident(
            incident_id=str(uuid4()),
            metric=metric,
            message=message,
            observed_value=float(observed_value),
            threshold_value=float(threshold_value),
            threshold_condition=threshold_condition,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        alert = SLOAlert(
            category=f"slo_violation_{metric}",
            message=message,
            payload={
                "incident_id": incident.incident_id,
                "metric": metric,
                "observed_value": observed_value,
                "threshold_value": threshold_value,
                "threshold_condition": threshold_condition,
            },
        )

        mitigation_triggered = False
        if self._mitigation_workflow is not None:
            self._mitigation_workflow(incident)
            mitigation_triggered = True

        incident = SLOIncident(
            incident_id=incident.incident_id,
            metric=incident.metric,
            message=incident.message,
            observed_value=incident.observed_value,
            threshold_value=incident.threshold_value,
            threshold_condition=incident.threshold_condition,
            created_at=incident.created_at,
            mitigation_triggered=mitigation_triggered,
            metadata=incident.metadata,
        )

        with self._lock:
            self._alerts.append(alert)
            self._incidents.append(incident)

        if self._alert_emitter is not None:
            self._alert_emitter(alert)

        if self._incident_recorder is not None:
            self._incident_recorder(incident)

        return incident

    def alerts(self) -> list[SLOAlert]:
        with self._lock:
            return list(self._alerts)

    def incidents(self) -> list[SLOIncident]:
        with self._lock:
            return list(self._incidents)
