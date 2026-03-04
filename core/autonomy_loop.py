"""Continuous autonomy loop orchestrating planning and execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from communication.message_bus import Message, MessageBus
from core.context_manager import ContextWindowConfig, LLMContextManager
from evaluation.auto_evaluator import AutoEvaluator
from governance.human_validation import HumanValidationController, HumanValidationError
from governance.policy_engine import PolicyEngine, PolicyViolationError
from learning.experience_store import ExperienceStore
from learning.performance_feedback import PerformanceFeedback
from memory.vector_memory import MemoryRecord, VectorMemory
from monitoring.alerts import AlertManager
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
        experience_store: ExperienceStore,
        performance_feedback: PerformanceFeedback,
        task_graph: TaskGraph,
        message_bus: MessageBus,
        auto_evaluator: AutoEvaluator | None = None,
        policy_engine: PolicyEngine | None = None,
        human_validation: HumanValidationController | None = None,
        alert_manager: AlertManager | None = None,
        llm_context_window_tokens: int = 8192,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.memory = memory
        self.experience_store = experience_store
        self.performance_feedback = performance_feedback
        self.task_graph = task_graph
        self.message_bus = message_bus
        self.auto_evaluator = auto_evaluator or AutoEvaluator(experience_store=experience_store)
        self.policy_engine = policy_engine
        self.human_validation = human_validation
        self.alert_manager = alert_manager
        self.context_manager = LLMContextManager(
            memory=memory,
            config=ContextWindowConfig(max_context_tokens=llm_context_window_tokens),
        )

    def run_cycle(self) -> dict:
        goals = self.planner.evaluate_active_goals()
        memory_context = self.memory.semantic_retrieve("active goals and historical outcomes", limit=12)
        prior_experience = self.experience_store.query_similar(
            " ".join(goals),
            limit=8,
            kinds={"task_outcome", "success_metrics", "evaluation", "execution_trace"},
        )
        combined_context = memory_context + [
            MemoryRecord(
                kind=record.kind,
                payload=record.payload,
                embedding=record.embedding,
                timestamp=record.timestamp,
            )
            for record in prior_experience
        ]
        combined_context = self.context_manager.prepare_planner_context(goals=goals, extra_records=combined_context)

        plan = self.planner.generate_plan(goals, combined_context)
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
            task_payload = {**task.payload, "task_id": task.task_id}
            try:
                if self.policy_engine is not None:
                    self.policy_engine.enforce(task_payload)
                if self.human_validation is not None:
                    self.human_validation.validate_task(task_id=task.task_id, payload=task.payload)
            except (PolicyViolationError, HumanValidationError) as error:
                result = {
                    "task_id": task.task_id,
                    "success": False,
                    "error": str(error),
                    "policy_violation": str(error),
                    "cost": 0.0,
                }
            else:
                result = self.executor.execute(task)

            executed += 1
            accumulated_cost += float(result.get("cost", 0.0))
            self.task_graph.mark_completed(task.task_id)
            self.memory.store_task_result(task.task_id, result)
            self.memory.store_agent_decision({"task_id": task.task_id, "decision": result.get("decision")})
            self.experience_store.store_task_outcome(task.task_id, result)
            self.experience_store.store_agent_decision(
                {
                    "task_id": task.task_id,
                    "decision": result.get("decision"),
                    "agent_id": result.get("agent_id"),
                }
            )
            self.experience_store.store_execution_trace(
                {
                    "task_id": task.task_id,
                    "status": result.get("status", "unknown"),
                    "tool": result.get("tool", result.get("tool_id")),
                    "cost": result.get("cost", 0.0),
                }
            )
            success = self.performance_feedback.record_execution({**result, "task_id": task.task_id})
            self.experience_store.store_success_metrics(
                {
                    "task_id": task.task_id,
                    "success": success,
                    "signals": self.performance_feedback.planner_signals(),
                }
            )

            primary_goal = goals[0] if goals else "autonomous execution"
            self.auto_evaluator.evaluate(goal=primary_goal, result=result)

            if self.alert_manager is not None:
                self.alert_manager.observe_result({**result, "task_id": task.task_id, "success": success})

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
