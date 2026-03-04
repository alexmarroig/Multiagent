"""Executor agent that performs concrete task work."""

from __future__ import annotations

from typing import Any


class ExecutorAgent:
    role = "executor"

    def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "task_id": task["task_id"],
            "status": "completed",
            "output": {"echo": task.get("description", "")},
            "cost": float(task.get("estimated_cost", 0.0)),
        }
