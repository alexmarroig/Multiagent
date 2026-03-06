"""Goal monitoring and progress evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GoalState:
    objective: str
    completion_keywords: list[str] = field(default_factory=list)
    status: str = "in_progress"
    progress: float = 0.0


class GoalManager:
    def __init__(self, objective: str, completion_keywords: list[str] | None = None) -> None:
        self.state = GoalState(objective=objective, completion_keywords=completion_keywords or [])

    def evaluate(self, latest_output: str) -> GoalState:
        if not latest_output:
            return self.state

        lowered = latest_output.lower()
        if any(keyword.lower() in lowered for keyword in self.state.completion_keywords):
            self.state.status = "completed"
            self.state.progress = 1.0
            return self.state

        self.state.progress = min(0.95, self.state.progress + 0.1)
        return self.state

    def is_completed(self) -> bool:
        return self.state.status == "completed"

    def metrics(self) -> dict[str, Any]:
        return {
            "objective": self.state.objective,
            "status": self.state.status,
            "progress": self.state.progress,
            "completion_keywords": self.state.completion_keywords,
        }
