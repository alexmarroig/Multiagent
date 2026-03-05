"""Guards against non-terminating planning and reflection loops."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class PlanningGuardLimits:
    max_loop_depth: int = 20
    max_repeated_plan_cycles: int = 5
    max_reflection_without_progress: int = 3


@dataclass(slots=True)
class AgentPlanningState:
    """Tracks planning behavior for one agent."""

    recent_plan_signatures: deque[str] = field(default_factory=lambda: deque(maxlen=32))
    loop_depth: int = 0
    reflection_streak_without_progress: int = 0


class PlanningGuard:
    """Terminates agents exhibiting repeated non-progress planning behavior."""

    def __init__(self, limits: PlanningGuardLimits | None = None) -> None:
        self.limits = limits or PlanningGuardLimits()
        self._states: dict[str, AgentPlanningState] = {}

    def record_cycle(self, agent_id: str, plan_signature: str, made_progress: bool) -> tuple[bool, str | None]:
        """Record one planning cycle and return whether agent should continue."""

        state = self._states.setdefault(agent_id, AgentPlanningState())
        state.loop_depth += 1
        state.recent_plan_signatures.append(plan_signature)

        if made_progress:
            state.reflection_streak_without_progress = 0
        else:
            state.reflection_streak_without_progress += 1

        if state.loop_depth > self.limits.max_loop_depth:
            return False, "loop_depth_exceeded"

        repeats = sum(1 for sig in state.recent_plan_signatures if sig == plan_signature)
        if repeats > self.limits.max_repeated_plan_cycles:
            return False, "repeated_planning_cycle"

        if state.reflection_streak_without_progress > self.limits.max_reflection_without_progress:
            return False, "reflection_without_progress"

        return True, None

    def terminate_agent(self, agent_id: str) -> None:
        """Drop tracking state after scheduler terminates an agent."""

        self._states.pop(agent_id, None)

    def metrics(self) -> dict[str, float]:
        depth = max((s.loop_depth for s in self._states.values()), default=0)
        return {"planning_loop_depth": float(depth)}
