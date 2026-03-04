"""Cluster-aware worker registry and scheduler for dynamic orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock


@dataclass(slots=True)
class WorkerRecord:
    """Live state for a worker in the cluster."""

    worker_id: str
    node_id: str
    capabilities: set[str] = field(default_factory=set)
    current_load: float = 0.0
    assigned_tasks: int = 0


@dataclass(slots=True)
class TaskAssignment:
    """Assignment details returned by the cluster scheduler."""

    worker_id: str
    node_id: str
    required_capability: str
    priority: int


class ClusterRegistry:
    """Tracks workers and schedules tasks by capability, load, and priority.

    Priorities are expected on a 0-100 scale where lower means more urgent.
    Workers can join and leave dynamically through register/unregister methods.
    """

    def __init__(self, *, low_priority_cutoff: int = 60, reserved_headroom: float = 0.25) -> None:
        self.low_priority_cutoff = max(0, min(100, low_priority_cutoff))
        self.reserved_headroom = max(0.0, min(1.0, reserved_headroom))
        self._workers: dict[str, WorkerRecord] = {}
        self._lock = RLock()

    def register_worker(
        self,
        *,
        worker_id: str,
        node_id: str,
        capabilities: set[str] | list[str] | tuple[str, ...],
        current_load: float = 0.0,
    ) -> WorkerRecord:
        with self._lock:
            record = WorkerRecord(
                worker_id=worker_id,
                node_id=node_id,
                capabilities=set(capabilities),
                current_load=max(0.0, current_load),
            )
            self._workers[worker_id] = record
            return record

    def unregister_worker(self, worker_id: str) -> bool:
        with self._lock:
            return self._workers.pop(worker_id, None) is not None

    def update_worker(
        self,
        worker_id: str,
        *,
        current_load: float | None = None,
        capabilities: set[str] | list[str] | tuple[str, ...] | None = None,
        node_id: str | None = None,
    ) -> WorkerRecord | None:
        with self._lock:
            record = self._workers.get(worker_id)
            if record is None:
                return None
            if current_load is not None:
                record.current_load = max(0.0, current_load)
            if capabilities is not None:
                record.capabilities = set(capabilities)
            if node_id is not None:
                record.node_id = node_id
            return record

    def schedule_task(self, *, required_capability: str, priority: int) -> TaskAssignment | None:
        with self._lock:
            worker = self._select_worker(required_capability=required_capability, priority=priority)
            if worker is None:
                return None
            worker.assigned_tasks += 1
            worker.current_load += 1
            return TaskAssignment(
                worker_id=worker.worker_id,
                node_id=worker.node_id,
                required_capability=required_capability,
                priority=priority,
            )

    def release_task(self, worker_id: str, *, load_reduction: float = 1.0) -> None:
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker is None:
                return
            worker.assigned_tasks = max(0, worker.assigned_tasks - 1)
            worker.current_load = max(0.0, worker.current_load - max(0.0, load_reduction))

    def snapshot(self) -> dict[str, dict[str, str | float | int | list[str]]]:
        with self._lock:
            return {
                worker.worker_id: {
                    "node_id": worker.node_id,
                    "capabilities": sorted(worker.capabilities),
                    "current_load": worker.current_load,
                    "assigned_tasks": worker.assigned_tasks,
                }
                for worker in self._workers.values()
            }

    def _select_worker(self, *, required_capability: str, priority: int) -> WorkerRecord | None:
        capable_workers = [w for w in self._workers.values() if required_capability in w.capabilities]
        if not capable_workers:
            return None

        normalized_priority = max(0, min(100, priority))
        if normalized_priority >= self.low_priority_cutoff:
            non_reserved = [w for w in capable_workers if w.current_load >= self.reserved_headroom]
            if non_reserved:
                capable_workers = non_reserved

        return min(capable_workers, key=lambda w: (w.current_load, w.assigned_tasks, w.worker_id))
