"""Scheduler for periodic autonomous agent execution."""

from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


class AgentScheduler:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()

    def queue_periodic_task(self, job_id: str, every_minutes: int, job_fn: Callable[[], None]) -> None:
        trigger = IntervalTrigger(minutes=max(1, every_minutes))
        self.scheduler.add_job(job_fn, trigger=trigger, id=job_id, replace_existing=True)

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
