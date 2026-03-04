"""Planner agent for high-level decomposition."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from learning.experience_store import ExperienceStore
from learning.strategy_optimizer import StrategyOptimizer


@dataclass(slots=True)
class Plan:
    objective: dict[str, Any]
    tasks: list[dict[str, Any]]


class PlannerAgent:
    role = "planner"

    def __init__(
        self,
        *,
        experience_store: ExperienceStore | None = None,
        strategy_optimizer: StrategyOptimizer | None = None,
    ) -> None:
        self.experience_store = experience_store
        self.strategy_optimizer = strategy_optimizer

    def create_plan(self, objective: dict[str, Any]) -> Plan:
        goal = str(objective.get("goal", "")).strip()

        if self.experience_store is not None and goal:
            objective["past_experiences"] = [
                record.payload for record in self.experience_store.retrieve_for_planning(goal, limit=5)
            ]

        tasks = objective.get("tasks") or [
            {"task_id": "bootstrap-1", "description": goal or "analyze objective", "priority": 50}
        ]

        if self.strategy_optimizer is not None:
            strategy_ids = [str(task.get("strategy_id", task.get("task_id"))) for task in tasks]
            ranked = self.strategy_optimizer.prioritize_strategies(strategy_ids)
            ranking = {item.strategy_id: item for item in ranked}
            tasks = sorted(tasks, key=lambda task: ranking[str(task.get("strategy_id", task.get("task_id")))].score, reverse=True)
            objective["strategy_scores"] = [asdict(item) for item in ranked]

        return Plan(objective=objective, tasks=tasks)
