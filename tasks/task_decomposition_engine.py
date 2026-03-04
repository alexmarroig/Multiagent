"""Task decomposition with hierarchical subtask generation."""

from __future__ import annotations

import uuid
from typing import Any


class TaskDecompositionEngine:
    def decompose(self, objective: dict[str, Any]) -> list[dict[str, Any]]:
        requested = objective.get("tasks", [])
        if requested:
            return requested
        goal = objective.get("goal", "deliver objective")
        return [
            {"task_id": f"task-{uuid.uuid4().hex[:8]}", "description": f"Plan: {goal}", "priority": 30},
            {"task_id": f"task-{uuid.uuid4().hex[:8]}", "description": f"Execute: {goal}", "priority": 50},
            {"task_id": f"task-{uuid.uuid4().hex[:8]}", "description": f"Verify: {goal}", "priority": 70},
        ]
