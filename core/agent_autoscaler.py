"""Autoscaling control plane for worker pools."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass(slots=True)
class ScalingMetrics:
    queue_depth: int
    worker_utilization: float
    task_latency_ms: float


class AgentAutoscaler:
    def __init__(
        self,
        *,
        min_workers: int = 1,
        max_workers: int = 20,
        target_utilization: float = 0.7,
        target_latency_ms: float = 500.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.target_utilization = target_utilization
        self.target_latency_ms = target_latency_ms
        self.logger = logger or logging.getLogger(__name__)

    def scale_up(self, current_workers: int, increment: int = 1) -> int:
        desired = min(self.max_workers, current_workers + max(1, increment))
        self.logger.info("autoscaler.scale_up", extra={"current_workers": current_workers, "desired_workers": desired})
        return desired

    def scale_down(self, current_workers: int, decrement: int = 1) -> int:
        desired = max(self.min_workers, current_workers - max(1, decrement))
        self.logger.info("autoscaler.scale_down", extra={"current_workers": current_workers, "desired_workers": desired})
        return desired

    def decide(self, metrics: ScalingMetrics, *, current_workers: int) -> int:
        if (
            metrics.queue_depth > current_workers
            or metrics.worker_utilization > self.target_utilization
            or metrics.task_latency_ms > self.target_latency_ms
        ):
            increment = max(1, metrics.queue_depth // max(current_workers, 1))
            return self.scale_up(current_workers, increment=increment)

        if metrics.queue_depth == 0 and metrics.worker_utilization < 0.2 and metrics.task_latency_ms < self.target_latency_ms * 0.5:
            return self.scale_down(current_workers, decrement=1)

        self.logger.info(
            "autoscaler.noop",
            extra={"queue_depth": metrics.queue_depth, "worker_utilization": metrics.worker_utilization, "task_latency_ms": metrics.task_latency_ms, "current_workers": current_workers},
        )
        return current_workers
