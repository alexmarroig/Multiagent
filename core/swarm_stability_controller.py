"""Monitors macro swarm health and applies stabilization policies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SwarmStabilityThresholds:
    max_agent_spawn_rate: float = 200.0
    max_queue_growth_rate: float = 100.0
    max_worker_saturation: float = 0.9


class SwarmStabilityController:
    """Detects collapse precursors and toggles defensive scheduling actions."""

    def __init__(self, thresholds: SwarmStabilityThresholds | None = None) -> None:
        self.thresholds = thresholds or SwarmStabilityThresholds()
        self.pause_new_spawns = False
        self.prioritize_active_tasks = False

    def evaluate(self, *, agent_spawn_rate: float, queue_growth_rate: float, worker_saturation: float) -> dict[str, bool]:
        """Evaluate health signals and update stabilization controls."""

        unstable = (
            agent_spawn_rate > self.thresholds.max_agent_spawn_rate
            or queue_growth_rate > self.thresholds.max_queue_growth_rate
            or worker_saturation > self.thresholds.max_worker_saturation
        )
        self.pause_new_spawns = unstable
        self.prioritize_active_tasks = unstable
        return {
            "instability_detected": unstable,
            "pause_new_spawns": self.pause_new_spawns,
            "prioritize_active_tasks": self.prioritize_active_tasks,
        }
