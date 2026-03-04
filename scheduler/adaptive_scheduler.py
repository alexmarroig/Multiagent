"""Adaptive scheduler for dynamic queue/worker/latency-aware task control."""

from __future__ import annotations

from collections import deque
"""Adaptive scheduler with runtime-aware safeguards against overload."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class SchedulerState:
    queue_depth: int = 0
    worker_utilization: float = 0.0
    average_latency_ms: float = 0.0
    max_parallel_tasks: int = 4
    worker_allocation: int = 4
    task_spawn_rate: float = 1.0
    low_priority_paused: bool = False
    overload_protection_active: bool = False


@dataclass(slots=True)
class SchedulerThresholds:
    queue_depth_high: int = 100
    queue_depth_critical: int = 250
    worker_utilization_low: float = 0.35
    worker_utilization_high: float = 0.9
    latency_high_ms: float = 3000.0


class AdaptiveScheduler:
    """Ranks tasks and adaptively tunes runtime limits to avoid overload."""

    def __init__(
        self,
        *,
        max_parallel_tasks: int = 4,
        worker_allocation: int | None = None,
        task_spawn_rate: float = 1.0,
        min_parallel_tasks: int = 1,
        max_parallel_ceiling: int = 64,
        min_spawn_rate: float = 0.1,
        max_spawn_rate: float = 5.0,
        thresholds: SchedulerThresholds | None = None,
        latency_window: int = 20,
    ) -> None:
        self.thresholds = thresholds or SchedulerThresholds()
        self.min_parallel_tasks = max(1, min_parallel_tasks)
        self.max_parallel_ceiling = max(self.min_parallel_tasks, max_parallel_ceiling)
        self.min_spawn_rate = max(0.01, min_spawn_rate)
        self.max_spawn_rate = max(self.min_spawn_rate, max_spawn_rate)
        self._latencies_ms: deque[float] = deque(maxlen=max(1, latency_window))
        initial_parallel = self._clamp_parallel(max_parallel_tasks)
        initial_allocation = worker_allocation if worker_allocation is not None else initial_parallel
        self._state = SchedulerState(
            max_parallel_tasks=initial_parallel,
            worker_allocation=self._clamp_parallel(initial_allocation),
            task_spawn_rate=self._clamp_spawn_rate(task_spawn_rate),
        )

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
            ranked = [task for task in ranked if int(task.get("priority", 50)) <= 50]
            ranked = [task for task in ranked if int(task.get("priority", 50)) < self.low_priority_cutoff]

        for task in ranked:
            task.setdefault("graph_id", graph_id)

        return ranked

    def adjust_limits(
        self,
        *,
        queue_depth: int | None = None,
        worker_utilization: float | None = None,
        task_latency_ms: float | None = None,
    ) -> dict[str, Any]:
        """Monitor runtime signals and adapt scheduling limits.

        Rules:
        - queue_depth > threshold_high: reduce spawning, pause low-priority tasks.
        - worker_utilization < threshold_low: increase parallelism.
        - high latency / critical pressure: aggressively throttle for overload safety.
        """

        if queue_depth is not None:
            self._state.queue_depth = max(0, int(queue_depth))
        if worker_utilization is not None:
            self._state.worker_utilization = self._clamp_percent(worker_utilization)
        if task_latency_ms is not None:
            latency = max(0.0, float(task_latency_ms))
            self._latencies_ms.append(latency)
            self._state.average_latency_ms = sum(self._latencies_ms) / len(self._latencies_ms)

        high_queue = self._state.queue_depth > self.thresholds.queue_depth_high
        critical_queue = self._state.queue_depth > self.thresholds.queue_depth_critical
        low_utilization = self._state.worker_utilization < self.thresholds.worker_utilization_low
        very_high_utilization = self._state.worker_utilization > self.thresholds.worker_utilization_high
        high_latency = self._state.average_latency_ms > self.thresholds.latency_high_ms

        self._state.low_priority_paused = False
        self._state.overload_protection_active = False

        if critical_queue or high_latency or very_high_utilization:
            # Hard safety mode to avoid overload spirals.
            self._state.overload_protection_active = True
            self._state.low_priority_paused = True
            self._state.max_parallel_tasks = self._clamp_parallel(self._state.max_parallel_tasks - 2)
            self._state.worker_allocation = self._clamp_parallel(self._state.worker_allocation - 1)
            self._state.task_spawn_rate = self._clamp_spawn_rate(self._state.task_spawn_rate * 0.6)
        elif high_queue:
            # Queue pressure: dampen ingress and reserve capacity for important work.
            self._state.low_priority_paused = True
            self._state.max_parallel_tasks = self._clamp_parallel(self._state.max_parallel_tasks - 1)
            self._state.task_spawn_rate = self._clamp_spawn_rate(self._state.task_spawn_rate * 0.8)
        elif low_utilization:
            # Under-used workers: safely scale up throughput.
            self._state.max_parallel_tasks = self._clamp_parallel(self._state.max_parallel_tasks + 1)
            self._state.worker_allocation = self._clamp_parallel(self._state.worker_allocation + 1)
            self._state.task_spawn_rate = self._clamp_spawn_rate(self._state.task_spawn_rate * 1.15)
        else:
            # Small convergence toward healthy defaults.
            self._state.worker_allocation = self._clamp_parallel(
                self._state.worker_allocation + (1 if self._state.worker_allocation < self._state.max_parallel_tasks else 0)
            )

        return self.get_scheduler_state()

    def get_scheduler_state(self) -> dict[str, Any]:
        return asdict(self._state)

    def _clamp_parallel(self, value: int) -> int:
        return max(self.min_parallel_tasks, min(self.max_parallel_ceiling, int(value)))

    def _clamp_spawn_rate(self, value: float) -> float:
        return max(self.min_spawn_rate, min(self.max_spawn_rate, float(value)))

    @staticmethod
    def _clamp_percent(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
