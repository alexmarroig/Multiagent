"""Adaptive scheduler that ranks candidate tasks by urgency and constraints."""

from __future__ import annotations

from typing import Any


class AdaptiveScheduler:
    def rank_candidates(self, *, graph_id: str, objective: dict[str, Any]) -> list[dict[str, Any]]:
        tasks = objective.get("tasks", [])
        ranked = sorted(tasks, key=lambda task: int(task.get("priority", 50)))
        for task in ranked:
            task.setdefault("graph_id", graph_id)
        return ranked
