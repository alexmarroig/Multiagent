"""Layered orchestration model for coordinator, worker, and utility agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.spawn_controller import SpawnController, SpawnRequest


class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    WORKER = "worker"
    UTILITY = "utility"


@dataclass(slots=True)
class AgentNode:
    agent_id: str
    role: AgentRole
    goal_id: str
    parent_agent_id: str | None = None
    recursion_depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class HierarchicalAgentOrchestrator:
    """Coordinates layered orchestration while enforcing bounded worker fan-out."""

    def __init__(self, spawn_controller: SpawnController) -> None:
        self.spawn_controller = spawn_controller
        self._agents: dict[str, AgentNode] = {}

    def register_agent(self, node: AgentNode) -> None:
        self._agents[node.agent_id] = node

    def plan_goal(self, coordinator_id: str, goal_id: str, tasks: list[dict[str, Any]]) -> list[str]:
        coordinator = self._agents[coordinator_id]
        if coordinator.role != AgentRole.COORDINATOR:
            raise ValueError("Only coordinator agents can plan goals")
        spawned: list[str] = []
        for idx, task in enumerate(tasks, start=1):
            worker_id = f"{goal_id}-worker-{idx:04d}"
            if self.spawn_worker(
                parent_agent_id=coordinator_id,
                worker_id=worker_id,
                goal_id=goal_id,
                recursion_depth=coordinator.recursion_depth + 1,
                metadata={"task": task},
            ):
                spawned.append(worker_id)
        return spawned

    def spawn_worker(
        self,
        *,
        parent_agent_id: str,
        worker_id: str,
        goal_id: str,
        recursion_depth: int,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        parent = self._agents[parent_agent_id]
        if parent.role == AgentRole.WORKER and recursion_depth > self.spawn_controller.limits.max_recursion_depth:
            return False
        request = SpawnRequest(
            goal_id=goal_id,
            parent_agent_id=parent_agent_id,
            agent_type=AgentRole.WORKER.value,
            recursion_depth=recursion_depth,
            metadata=metadata or {},
        )
        if not self.spawn_controller.request_spawn(request):
            return False
        self._agents[worker_id] = AgentNode(
            agent_id=worker_id,
            role=AgentRole.WORKER,
            goal_id=goal_id,
            parent_agent_id=parent_agent_id,
            recursion_depth=recursion_depth,
            metadata=metadata or {},
        )
        return True

    def aggregate_results(self, coordinator_id: str, worker_outputs: list[dict[str, Any]]) -> dict[str, Any]:
        coordinator = self._agents[coordinator_id]
        if coordinator.role != AgentRole.COORDINATOR:
            raise ValueError("Only coordinator agents can aggregate results")
        return {
            "goal_id": coordinator.goal_id,
            "workers": len(worker_outputs),
            "summary": [item.get("result") for item in worker_outputs],
        }

    def run_utility_validation(self, utility_id: str, aggregated: dict[str, Any]) -> dict[str, Any]:
        utility = self._agents[utility_id]
        if utility.role != AgentRole.UTILITY:
            raise ValueError("Only utility agents can run validation")
        aggregated["validated"] = bool(aggregated.get("summary"))
        return aggregated
