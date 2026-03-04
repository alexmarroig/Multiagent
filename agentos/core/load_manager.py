"""Distributed worker load management and placement heuristics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkerLoad:
    worker_id: str
    cpu_load: float
    memory_load: float
    queue_depth: int
    active_tasks: int


class LoadManager:
    def __init__(self) -> None:
        self._workers: dict[str, WorkerLoad] = {}

    def update_worker(self, load: WorkerLoad) -> None:
        self._workers[load.worker_id] = load

    def select_worker(self) -> str | None:
        if not self._workers:
            return None
        return min(
            self._workers.values(),
            key=lambda w: (w.active_tasks, w.queue_depth, w.cpu_load + w.memory_load),
        ).worker_id

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        return {
            worker_id: {
                "cpu_load": state.cpu_load,
                "memory_load": state.memory_load,
                "queue_depth": state.queue_depth,
                "active_tasks": state.active_tasks,
            }
            for worker_id, state in self._workers.items()
        }
