"""Scheduling kernel connecting graph state to adaptive schedulers."""

from __future__ import annotations

from typing import Any

from agentos.scheduler.adaptive_scheduler import AdaptiveScheduler
from agentos.scheduler.queue_backpressure_controller import QueueBackpressureController


class SchedulingKernel:
    def __init__(
        self,
        *,
        adaptive_scheduler: AdaptiveScheduler,
        backpressure: QueueBackpressureController,
    ) -> None:
        self.adaptive_scheduler = adaptive_scheduler
        self.backpressure = backpressure

    def generate_plan(self, graph_id: str, objective: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = self.adaptive_scheduler.rank_candidates(graph_id=graph_id, objective=objective)
        return self.backpressure.apply(candidates)
