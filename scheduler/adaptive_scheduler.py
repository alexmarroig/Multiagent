"""Adaptive scheduler with runtime-aware safeguards against overload."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class SchedulerState:
    queue_depth: int
    worker_utilization: float
    task_latency_ms: float
    max_parallel_tasks: int
    worker_allocation: int
    task_spawn_rate: int
    low_priority_paused: bool
    overload_protection_active: bool


class AdaptiveScheduler:
    def __init__(
        self,
        *,
        queue_depth_threshold_high: int = 100,
        queue_depth_threshold_critical: int = 200,
        worker_utilization_threshold_low: float = 0.35,
        worker_utilization_threshold_high: float = 0.9,
        latency_threshold_ms: float = 1_500.0,
        latency_critical_threshold_ms: float = 3_000.0,
        initial_max_parallel_tasks: int = 16,
        initial_worker_allocation: int = 4,
        initial_task_spawn_rate: int = 20,
        min_parallel_tasks: int = 1,
        max_parallel_tasks_cap: int = 64,
        min_worker_allocation: int = 1,
        max_worker_allocation: int = 32,
        min_task_spawn_rate: int = 1,
        max_task_spawn_rate: int = 100,
        low_priority_cutoff: int = 70,
    ) -> None:
        self.queue_depth_threshold_high = queue_depth_threshold_high
        self.queue_depth_threshold_critical = max(queue_depth_threshold_critical, queue_depth_threshold_high)
        self.worker_utilization_threshold_low = worker_utilization_threshold_low
        self.worker_utilization_threshold_high = max(worker_utilization_threshold_high, worker_utilization_threshold_low)
        self.latency_threshold_ms = latency_threshold_ms
        self.latency_critical_threshold_ms = max(latency_critical_threshold_ms, latency_threshold_ms)

        self.min_parallel_tasks = min_parallel_tasks
        self.max_parallel_tasks_cap = max(max_parallel_tasks_cap, min_parallel_tasks)
        self.min_worker_allocation = min_worker_allocation
        self.max_worker_allocation = max(max_worker_allocation, min_worker_allocation)
        self.min_task_spawn_rate = min_task_spawn_rate
        self.max_task_spawn_rate = max(max_task_spawn_rate, min_task_spawn_rate)
        self.low_priority_cutoff = low_priority_cutoff

        self._state = SchedulerState(
            queue_depth=0,
            worker_utilization=0.0,
            task_latency_ms=0.0,
            max_parallel_tasks=self._clamp(initial_max_parallel_tasks, self.min_parallel_tasks, self.max_parallel_tasks_cap),
            worker_allocation=self._clamp(initial_worker_allocation, self.min_worker_allocation, self.max_worker_allocation),
            task_spawn_rate=self._clamp(initial_task_spawn_rate, self.min_task_spawn_rate, self.max_task_spawn_rate),
            low_priority_paused=False,
            overload_protection_active=False,
        )

    @staticmethod
    def _clamp(value: int, lower: int, upper: int) -> int:
        return max(lower, min(upper, value))

    def observe_metrics(self, *, queue_depth: int, worker_utilization: float, task_latency_ms: float) -> dict[str, Any]:
        """Record current runtime metrics and adapt scheduling limits."""
        return self.adjust_limits(
            queue_depth=queue_depth,
            worker_utilization=worker_utilization,
            task_latency_ms=task_latency_ms,
        )

    def adjust_limits(
        self,
        *,
        queue_depth: int | None = None,
        worker_utilization: float | None = None,
        task_latency_ms: float | None = None,
    ) -> dict[str, Any]:
        """Dynamically adjust scheduler limits to maximize throughput without overload."""
        if queue_depth is not None:
            self._state.queue_depth = max(0, queue_depth)
        if worker_utilization is not None:
            self._state.worker_utilization = max(0.0, min(1.0, worker_utilization))
        if task_latency_ms is not None:
            self._state.task_latency_ms = max(0.0, task_latency_ms)

        queue_high = self._state.queue_depth > self.queue_depth_threshold_high
        queue_critical = self._state.queue_depth > self.queue_depth_threshold_critical
        latency_high = self._state.task_latency_ms > self.latency_threshold_ms
        latency_critical = self._state.task_latency_ms > self.latency_critical_threshold_ms
        utilization_low = self._state.worker_utilization < self.worker_utilization_threshold_low
        utilization_high = self._state.worker_utilization > self.worker_utilization_threshold_high

        if queue_high:
            self._state.task_spawn_rate = self._clamp(
                self._state.task_spawn_rate - 3,
                self.min_task_spawn_rate,
                self.max_task_spawn_rate,
            )
            self._state.low_priority_paused = True

        if utilization_low:
            self._state.max_parallel_tasks = self._clamp(
                self._state.max_parallel_tasks + 2,
                self.min_parallel_tasks,
                self.max_parallel_tasks_cap,
            )
            self._state.worker_allocation = self._clamp(
                self._state.worker_allocation + 1,
                self.min_worker_allocation,
                self.max_worker_allocation,
            )
            if not queue_high:
                self._state.task_spawn_rate = self._clamp(
                    self._state.task_spawn_rate + 2,
                    self.min_task_spawn_rate,
                    self.max_task_spawn_rate,
                )

        if latency_high or utilization_high:
            self._state.task_spawn_rate = self._clamp(
                self._state.task_spawn_rate - 1,
                self.min_task_spawn_rate,
                self.max_task_spawn_rate,
            )

        if queue_critical or latency_critical:
            self._state.max_parallel_tasks = self._clamp(
                self._state.max_parallel_tasks - 2,
                self.min_parallel_tasks,
                self.max_parallel_tasks_cap,
            )
            self._state.task_spawn_rate = self._clamp(
                self._state.task_spawn_rate - 5,
                self.min_task_spawn_rate,
                self.max_task_spawn_rate,
            )

        if not queue_high and not latency_high:
            self._state.low_priority_paused = False

        self._state.overload_protection_active = queue_high or latency_high
        return self.get_scheduler_state()

    def get_scheduler_state(self) -> dict[str, Any]:
        """Expose current scheduler state for observability and control-plane APIs."""
        return asdict(self._state)

    def rank_candidates(self, *, graph_id: str, objective: dict[str, Any]) -> list[dict[str, Any]]:
        """Prioritize tasks and enforce low-priority pausing during overload."""
        tasks = objective.get("tasks", [])
        ranked = sorted(tasks, key=lambda task: int(task.get("priority", 50)))

        if self._state.low_priority_paused:
            ranked = [task for task in ranked if int(task.get("priority", 50)) < self.low_priority_cutoff]

        for task in ranked:
            task.setdefault("graph_id", graph_id)
        return ranked
