"""Autonomy manager maintaining continuous distributed execution loops."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from core.task_queue import DistributedTaskQueue
from tasks.task_graph_engine import TaskGraphEngine


class GoalEvaluator(Protocol):
    def evaluate_goals(self) -> list[dict]: ...


class Planner(Protocol):
    def generate_plan(self, goals: list[dict]) -> list[dict]: ...


@dataclass(slots=True)
class AutonomyTickResult:
    goals: int
    tasks_enqueued: int


class AutonomyManager:
    """Monitors goals, spawns tasks, and continuously triggers distributed workers."""

    def __init__(
        self,
        *,
        goal_evaluator: GoalEvaluator,
        planner: Planner,
        task_graph_engine: TaskGraphEngine,
        task_queue: DistributedTaskQueue,
        tick_interval_seconds: float = 0.5,
    ) -> None:
        self.goal_evaluator = goal_evaluator
        self.planner = planner
        self.task_graph_engine = task_graph_engine
        self.task_queue = task_queue
        self.tick_interval_seconds = max(0.05, tick_interval_seconds)

    def run_once(self) -> AutonomyTickResult:
        goals = self.goal_evaluator.evaluate_goals()
        plan = self.planner.generate_plan(goals)
        self.task_graph_engine.ingest_plan(plan)
        scheduled = self.task_graph_engine.schedule_ready_tasks()
        return AutonomyTickResult(goals=len(goals), tasks_enqueued=len(scheduled))

    def run_loop(self, *, max_iterations: int | None = None) -> None:
        iterations = 0
        while True:
            self.run_once()
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(self.tick_interval_seconds)
