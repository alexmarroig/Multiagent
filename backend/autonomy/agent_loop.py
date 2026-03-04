"""Autonomous planning loop with guardrails."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from agents.communication_bus import CommunicationBus
from goals.goal_manager import GoalManager
from memory.vector_memory import VectorMemory
from autonomy.task_decomposer import TaskDecomposer
from orchestrator.task_queue import QueuedTask, TaskQueue


@dataclass
class LoopGuardrails:
    max_iterations: int = 8
    max_runtime_seconds: int = 900
    max_cost: float = 5.0


class AutonomousAgentLoop:
    def __init__(
        self,
        *,
        session_id: str,
        objective: str,
        execute_fn: Callable[[dict[str, Any]], Any],
        planner_fn: Callable[[str, list[dict[str, Any]]], list[QueuedTask]],
        guardrails: LoopGuardrails | None = None,
        completion_keywords: list[str] | None = None,
    ) -> None:
        self.session_id = session_id
        self.execute_fn = execute_fn
        self.planner_fn = planner_fn
        self.guardrails = guardrails or LoopGuardrails()
        self.goal_manager = GoalManager(objective=objective, completion_keywords=completion_keywords)
        self.memory = VectorMemory(session_id=session_id)
        self.task_queue = TaskQueue()
        self.bus = CommunicationBus()
        self.accumulated_cost = 0.0
        self.decomposer = TaskDecomposer()

    def _evaluate_current_state(self) -> list[dict[str, Any]]:
        return self.memory.retrieve_context(limit=20)

    def _plan_new_tasks(self, context: list[dict[str, Any]]) -> None:
        planned = self.planner_fn(self.goal_manager.state.objective, context)
        for task in planned:
            self.task_queue.enqueue(task)

    def _execute_tasks(self) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []

        while len(self.task_queue) > 0:
            task = self.task_queue.dequeue()
            if task is None:
                break

            inbox_message = self.bus.receive(task.agent_id)
            payload = {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "description": task.description,
                "payload": task.payload,
                "message": inbox_message,
            }
            result = self.execute_fn(payload)
            output = {
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "description": task.description,
                "result": str(result),
            }
            outputs.append(output)
            self.memory.store_task_result(task.task_id, output)

            discovered_work = result.get("spawn_tasks", []) if isinstance(result, dict) else []
            for spawned_task in self.decomposer.generate_dynamic_subtasks(
                session_id=self.session_id,
                parent_task_id=task.task_id,
                discovered_work=discovered_work,
            ):
                self.task_queue.enqueue(spawned_task)

            delegate_to = task.payload.get("delegate_to")
            if delegate_to:
                self.bus.send_message(delegate_to, {"from": task.agent_id, "task_result": output})

        return outputs

    def run(self) -> dict[str, Any]:
        started = time.monotonic()
        iteration = 0
        last_outputs: list[dict[str, Any]] = []

        while not self.goal_manager.is_completed():
            if iteration >= self.guardrails.max_iterations:
                break
            if time.monotonic() - started > self.guardrails.max_runtime_seconds:
                break
            if self.accumulated_cost >= self.guardrails.max_cost:
                break

            context = self._evaluate_current_state()
            self._plan_new_tasks(context)
            outputs = self._execute_tasks()
            last_outputs = outputs

            summary = "\n".join(item.get("result", "") for item in outputs)
            state = self.goal_manager.evaluate(summary)
            self.memory.store_event({"iteration": iteration, "state": state.status, "progress": state.progress})

            # custo aproximado baseado em quantidade de tarefas executadas
            self.accumulated_cost += 0.05 * max(1, len(outputs))
            iteration += 1

        return {
            "status": "completed" if self.goal_manager.is_completed() else "stopped",
            "iterations": iteration,
            "cost": round(self.accumulated_cost, 4),
            "goal": self.goal_manager.metrics(),
            "last_outputs": last_outputs,
        }
