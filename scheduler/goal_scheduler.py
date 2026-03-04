"""Goal scheduler for periodic goal checks, retries, and background processing."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class ScheduledGoal:
    name: str
    callback: Callable[[], None]
    interval_seconds: int
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0
    last_run: float = 0.0
    retry_count: int = 0
    enabled: bool = True


class GoalScheduler:
    def __init__(self) -> None:
        self._goals: dict[str, ScheduledGoal] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def add_periodic_task_generation(self, name: str, callback: Callable[[], None], interval_seconds: int) -> None:
        self._goals[name] = ScheduledGoal(name=name, callback=callback, interval_seconds=max(1, interval_seconds))

    def add_goal_monitoring(self, callback: Callable[[], None], interval_seconds: int = 30) -> None:
        self.add_periodic_task_generation("goal_monitoring", callback, interval_seconds)

    def _run_goal(self, goal: ScheduledGoal) -> None:
        try:
            goal.callback()
            goal.retry_count = 0
        except Exception:  # noqa: BLE001
            goal.retry_count += 1
            if goal.retry_count > goal.max_retries:
                goal.enabled = False
            else:
                time.sleep(goal.retry_backoff_seconds * goal.retry_count)
        finally:
            goal.last_run = time.monotonic()

    def _run(self) -> None:
        while self._running:
            now = time.monotonic()
            for goal in self._goals.values():
                if not goal.enabled:
                    continue
                if now - goal.last_run >= goal.interval_seconds:
                    self._run_goal(goal)
            time.sleep(0.2)

    def start_background_execution(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
