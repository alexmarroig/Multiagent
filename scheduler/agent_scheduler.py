"""Scheduler for periodic tasks, goal monitoring, agent restarts, and background runtime execution."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class ScheduledTask:
    name: str
    interval_seconds: int
    callback: Callable[[], None]
    last_run: float = 0.0


class AgentScheduler:
    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def add_periodic_task(self, name: str, interval_seconds: int, callback: Callable[[], None]) -> None:
        self._tasks[name] = ScheduledTask(name=name, interval_seconds=max(1, interval_seconds), callback=callback)

    def add_goal_monitor(self, callback: Callable[[], None], interval_seconds: int = 30) -> None:
        self.add_periodic_task("goal_monitor", interval_seconds, callback)

    def add_agent_restart(self, callback: Callable[[], None], interval_seconds: int = 60) -> None:
        self.add_periodic_task("agent_restart", interval_seconds, callback)

    def _run(self) -> None:
        while self._running:
            now = time.monotonic()
            for task in self._tasks.values():
                if now - task.last_run >= task.interval_seconds:
                    task.callback()
                    task.last_run = now
            time.sleep(0.25)

    def start_background(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
