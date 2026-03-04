from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy.agent_loop import AutonomousAgentLoop
from autonomy.agent_loop import LoopGuardrails
from autonomy.task_decomposer import DecompositionConstraints, TaskDecomposer
from orchestrator.task_queue import QueuedTask


class InMemoryContext:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def retrieve_context(self, limit: int = 20) -> list[dict]:
        return self.items[-limit:]

    def store_task_result(self, task_id: str, output: dict) -> None:
        self.items.append({"kind": "task_result", "payload": {"task_id": task_id, "output": output}})

    def store_event(self, payload: dict) -> None:
        self.items.append({"kind": "event", "payload": payload})


def test_decomposer_builds_hierarchy_with_limits() -> None:
    decomposer = TaskDecomposer(
        DecompositionConstraints(max_depth=2, max_subtasks_per_task=2, max_total_tasks=6, max_task_tokens=20)
    )

    tasks = decomposer.decompose(
        objective=(
            "Planejar arquitetura do serviço, implementar endpoints da API, "
            "escrever testes automatizados e gerar relatório técnico"
        ),
        session_id="s-1",
        context=[],
    )

    assert 1 < len(tasks) <= 6
    assert all(task.estimated_complexity >= 1 for task in tasks)
    assert all(task.expected_output_format for task in tasks)
    assert all(isinstance(task.required_tools, list) and task.required_tools for task in tasks)

    by_id = {task.task_id: task for task in tasks}
    depths = [int(task.payload.get("depth", 0)) for task in tasks]
    assert max(depths) <= 2

    for task in tasks:
        parent = task.parent_task_id
        if parent is not None:
            assert parent in by_id


def test_agent_loop_enqueues_dynamic_subtasks_from_execution_result() -> None:
    planned = [
        QueuedTask(
            task_id="s-loop-t1",
            agent_id="supervisor",
            description="Executar primeira etapa",
            payload={"objective": "Executar primeira etapa"},
        )
    ]

    def planner_fn(_objective: str, _context: list[dict]) -> list[QueuedTask]:
        return planned

    call_count = {"value": 0}

    def execute_fn(_payload: dict) -> dict:
        call_count["value"] += 1
        if call_count["value"] == 1:
            return {
                "status": "ok",
                "spawn_tasks": [
                    {
                        "description": "Investigar erro de integração recém-descoberto",
                        "agent_id": "supervisor",
                        "expected_output_format": "json",
                    }
                ],
            }
        return {"status": "ok", "spawn_tasks": []}

    loop = AutonomousAgentLoop(
        session_id="s-loop",
        objective="Resolver objetivo complexo",
        execute_fn=execute_fn,
        planner_fn=planner_fn,
        guardrails=LoopGuardrails(max_iterations=1),
    )
    loop.memory = InMemoryContext()

    result = loop.run()

    assert result["iterations"] >= 1
    assert any("Investigar erro de integração" in item.get("description", "") for item in result["last_outputs"])
