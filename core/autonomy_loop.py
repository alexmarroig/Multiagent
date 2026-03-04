"""Continuous autonomy loop orchestrating planning and execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from communication.message_bus import Message, MessageBus
from memory.vector_memory import MemoryRecord, VectorMemory
from tasks.task_graph import TaskGraph, TaskNode


class Planner(Protocol):
    def evaluate_active_goals(self) -> list[str]:
        ...

    def generate_plan(self, goals: list[str], memory_context: list[MemoryRecord]) -> list[dict]:
        ...

    def update_goals(self, execution_summary: dict) -> None:
        ...


class TaskExecutor(Protocol):
    def execute(self, task: TaskNode) -> dict:
        ...


@dataclass(slots=True)
class LoopResult:
    executed_tasks: int
    cost: float
    halt: bool = False


class AutonomousPlanningLoop:
    """Implements: evaluate goals → plan → decompose → execute → review → store → update."""

    def __init__(
        self,
        *,
        planner: Planner,
        executor: TaskExecutor,
        memory: VectorMemory,
        task_graph: TaskGraph,
        message_bus: MessageBus,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.memory = memory
        self.task_graph = task_graph
        self.message_bus = message_bus

    def run_cycle(self) -> dict:
        goals = self.planner.evaluate_active_goals()
        memory_context = self.memory.semantic_retrieve("active goals and historical outcomes", limit=12)

        plan = self.planner.generate_plan(goals, memory_context)
        for item in plan:
            self.task_graph.add_task(
                task_id=item["task_id"],
                description=item.get("description", "planned task"),
                priority=item.get("priority", 50),
                required_skill=item.get("required_skill"),
                dependencies=item.get("dependencies", []),
                payload=item.get("payload", {}),
            )

        executed = 0
        accumulated_cost = 0.0
        for task in self.task_graph.get_ready_tasks():
            result = self.executor.execute(task)
            executed += 1
            accumulated_cost += float(result.get("cost", 0.0))
            self.task_graph.mark_completed(task.task_id)
            self.memory.store_task_result(task.task_id, result)
            self.memory.store_agent_decision({"task_id": task.task_id, "decision": result.get("decision")})

            if delegated := result.get("delegate_to"):
                self.message_bus.delegate_task(
                    from_agent=result.get("agent_id", "unknown"),
                    to_agent=delegated,
                    task_id=task.task_id,
                    payload=result,
                )

            if spawned := result.get("spawn_tasks", []):
                for node in spawned:
                    self.task_graph.spawn_task(parent_task_id=task.task_id, **node)

        review = {"executed": executed, "remaining": self.task_graph.pending_count()}
        self.memory.store_knowledge({"cycle_review": review, "goals": goals})
        self.memory.store_environment_state({"bus_depth": self.message_bus.depth(), "pending_tasks": review["remaining"]})
        self.planner.update_goals(review)

        if executed == 0 and self.task_graph.pending_count() == 0:
            self.message_bus.broadcast(Message(topic="autonomy.idle", payload={"goals": goals}))
            return LoopResult(executed_tasks=0, cost=0.0, halt=True).__dict__

        return LoopResult(executed_tasks=executed, cost=accumulated_cost).__dict__
