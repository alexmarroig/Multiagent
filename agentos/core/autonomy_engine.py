"""Autonomy engine responsible for adaptive execution loops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentos.communication.event_bus import EventBus
from agentos.monitoring.telemetry_service import TelemetryService
from tasks.task_checkpoint_store import TaskCheckpointStore


@dataclass(slots=True)
class ExecutionWindow:
    max_parallelism: int
    max_retries: int
    timeout_seconds: int


class AutonomyEngine:
    def __init__(
        self,
        *,
        checkpoint_store: TaskCheckpointStore,
        event_bus: EventBus,
        telemetry: TelemetryService,
    ) -> None:
        self.checkpoint_store = checkpoint_store
        self.event_bus = event_bus
        self.telemetry = telemetry

    def execute(self, *, graph_id: str, schedule: list[dict[str, Any]]) -> dict[str, Any]:
        self.telemetry.record("autonomy.execution.started", {"graph_id": graph_id, "tasks": len(schedule)})
        completed = 0
        for item in schedule:
            checkpoint = {
                "graph_id": graph_id,
                "task_id": item["task_id"],
                "worker_id": item.get("worker_id"),
                "status": "completed",
            }
            self.checkpoint_store.write(checkpoint)
            self.event_bus.publish("task.completed", checkpoint)
            completed += 1
        report = {"graph_id": graph_id, "scheduled": len(schedule), "completed": completed}
        self.telemetry.record("autonomy.execution.completed", report)
        return report
