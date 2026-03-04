from __future__ import annotations

import random

from agentos.communication.message_bus import MessageBus
from agentos.core.autonomy_loop import AutonomousPlanningLoop
from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from learning.experience_store import ExperienceStore
from learning.performance_feedback import PerformanceFeedback
from memory.vector_memory import MemoryRecord, VectorMemory
from tasks.task_graph import TaskGraph


class _Planner:
    def evaluate_active_goals(self) -> list[str]:
        return ["resilience"]

    def generate_plan(self, goals, memory_context) -> list[dict]:
        return [{"task_id": "fuzz-task", "description": "handle malformed tool output"}]

    def update_goals(self, execution_summary: dict) -> None:
        return None


class _MalformedExecutor:
    def execute(self, task):
        return random.choice(["bad-output", 42, ["not", "a", "dict"], None])


def test_fuzz_invalid_task_inputs_do_not_break_queue() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=1)
    invalid_inputs = [
        {"task_id": None, "name": "invalid-none-id", "payload": "not-a-dict"},
        {"task_id": "invalid-priority", "name": "invalid", "priority": "high"},
        {"task_id": "invalid-dependencies", "name": "invalid", "dependencies": "dep-1"},
    ]

    for payload in invalid_inputs:
        try:
            queue.enqueue_task(payload)
        except (TypeError, ValueError):
            pass

    queue.enqueue_task({"task_id": "valid-task", "name": "recovery", "payload": {"ok": True}})

    recovered_task = None
    while queue.queue_size() > 0:
        dequeued = queue.dequeue_task()
        if dequeued is None:
            break
        if dequeued.task_id == "valid-task":
            recovered_task = dequeued
            break

    assert recovered_task is not None


def test_fuzz_malformed_tool_responses_are_normalized() -> None:
    loop = AutonomousPlanningLoop(
        planner=_Planner(),
        executor=_MalformedExecutor(),
        memory=VectorMemory(),
        experience_store=ExperienceStore(),
        performance_feedback=PerformanceFeedback(),
        task_graph=TaskGraph(),
        message_bus=MessageBus(),
    )

    result = loop.run_cycle()

    assert result["executed_tasks"] == 1
    assert result["cost"] == 0.0


def test_fuzz_random_memory_corruption_keeps_retrieval_stable() -> None:
    memory = VectorMemory()
    memory.store_knowledge({"seed": "stable-record"})

    for idx in range(20):
        if random.random() < 0.5:
            memory._records.append(f"corrupt-{idx}")
        else:
            memory._records.append(
                MemoryRecord(kind="knowledge", payload={"idx": idx}, embedding=["nan", None], timestamp="corrupt")
            )

    retrieved = memory.semantic_retrieve("stable-record", limit=3)

    assert len(retrieved) >= 1
    assert all(isinstance(record, MemoryRecord) for record in retrieved)
