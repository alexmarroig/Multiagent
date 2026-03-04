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
        try:
            self.memory = VectorMemory(session_id=session_id)
        except TypeError:
            self.memory = VectorMemory()
        self.task_queue = TaskQueue()
        self.bus = CommunicationBus()
        self.accumulated_cost = 0.0
        self.decomposer = TaskDecomposer()

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def _summarize_context(self, context: list[dict[str, Any]], token_budget: int) -> dict[str, Any] | None:
        if not context:
            return None

        consumed = 0
        snippets: list[str] = []
        for item in context:
            payload = item.get("payload", item)
            snippet = str(payload)[:400]
            snippet_tokens = self._estimate_tokens(snippet)
            if consumed + snippet_tokens > token_budget:
                break
            snippets.append(snippet)
            consumed += snippet_tokens

        if not snippets:
            return None

        return {
            "metadata": {"kind": "summary", "source_items": len(snippets)},
            "payload": {"summary": " | ".join(snippets)},
        }

    def _prepare_planner_context(self, objective: str, context: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # 1) Retrieve relevant memory for this objective.
        semantic_hits: list[dict[str, Any]] = []
        if hasattr(self.memory, "semantic_search"):
            semantic_hits = list(self.memory.semantic_search(objective, limit=8))

        normalized_hits = [
            {"metadata": item.get("metadata", {}), "payload": item.get("document", item.get("payload", {}))}
            for item in semantic_hits
        ]
        all_items = context + normalized_hits

        # 2) Summarize long histories to preserve key information in limited windows.
        compact: list[dict[str, Any]] = []
        long_items: list[dict[str, Any]] = []
        for item in all_items:
            tokens = self._estimate_tokens(str(item.get("payload", item)))
            if tokens > 180:
                long_items.append(item)
            else:
                compact.append(item)

        summary = self._summarize_context(long_items, token_budget=220)
        if summary is not None:
            compact.append(summary)

        # 3) Truncate low-priority context when over budget.
        compact = sorted(
            compact,
            key=lambda item: 0 if item.get("metadata", {}).get("kind") == "summary" else 1,
        )
        budget = 700
        selected: list[dict[str, Any]] = []
        used = 0
        for item in compact:
            tokens = self._estimate_tokens(str(item.get("payload", item)))
            if used + tokens > budget:
                continue
            selected.append(item)
            used += tokens

        # 4) Assemble final context.
        return selected

    def _evaluate_current_state(self) -> list[dict[str, Any]]:
        return self.memory.retrieve_context(limit=20)

    def _plan_new_tasks(self, context: list[dict[str, Any]]) -> None:
        llm_context = self._prepare_planner_context(self.goal_manager.state.objective, context)
        planned = self.planner_fn(self.goal_manager.state.objective, llm_context)
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
