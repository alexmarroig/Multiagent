"""Queue backpressure controller for adaptive throughput limiting."""

from __future__ import annotations


class QueueBackpressureController:
    def __init__(self, max_dispatch: int = 100) -> None:
        self.max_dispatch = max_dispatch

    def apply(self, scheduled_tasks: list[dict]) -> list[dict]:
        return scheduled_tasks[: self.max_dispatch]
