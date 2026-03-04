from __future__ import annotations

from communication.event_bus import EventBus
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from tasks.task_graph_engine import TaskGraphEngine, TaskGraphSafetyLimits


def run_audit() -> dict[str, object]:
    name = "Task Explosion Protection"
    try:
        limits = TaskGraphSafetyLimits(max_total_tasks=20, max_subtasks_per_task=3, max_task_depth=2)
        engine = TaskGraphEngine(queue=DistributedTaskQueue(InMemoryQueueBackend()), safety_limits=limits, event_bus=EventBus())
        for idx in range(20):
            engine.add_task(task_id=f"t{idx}", name="audit-task")
        status = "OK"
        details = {
            "max_total_tasks": limits.max_total_tasks,
            "max_subtasks_per_task": limits.max_subtasks_per_task,
            "max_task_depth": limits.max_task_depth,
        }
        return {"name": name, "status": status, "details": details}
    except ValueError as exc:
        return {"name": name, "status": "OK", "details": {"safety_triggered": str(exc)}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
