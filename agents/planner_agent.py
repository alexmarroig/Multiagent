"""Planner agent for high-level decomposition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Plan:
    objective: dict[str, Any]
    tasks: list[dict[str, Any]]


class PlannerAgent:
    role = "planner"

    def create_plan(self, objective: dict[str, Any]) -> Plan:
        tasks = objective.get("tasks") or [
            {"task_id": "bootstrap-1", "description": objective.get("goal", "analyze objective"), "priority": 50}
        ]
        return Plan(objective=objective, tasks=tasks)
