from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph_planner import (
    MAX_DECOMPOSITION_DEPTH,
    MAX_SUBTASKS_PER_TASK,
    generate_dynamic_subtasks,
    generate_plan,
)


def test_generate_plan_adds_core_tasks_in_order():
    plan_md, tasks = generate_plan("Melhorar API")

    assert "# Plano para: Melhorar API" in plan_md
    assert [task["order_index"] for task in tasks] == list(range(len(tasks)))
    assert [task["title"] for task in tasks[:3]] == [
        "Analisar Contexto",
        "Implementar Solução",
        "Validar Entrega",
    ]
    assert all("task_id" in task for task in tasks)
    assert all("estimated_complexity" in task for task in tasks)
    assert all("required_tools" in task for task in tasks)
    assert all("expected_output_format" in task for task in tasks)
    assert "id=task-1" in plan_md


def test_generate_plan_matches_quality_and_ci_keywords():
    _, tasks = generate_plan(
        "Criar testes de regressão, monitoramento em tempo real e integração contínua no pipeline"
    )

    task_titles = {task["title"] for task in tasks}
    assert "Criar e Automatizar Testes" in task_titles
    assert "Monitoramento Inteligente e Anomalias" in task_titles
    assert "Integrar Qualidade ao Pipeline CI" in task_titles


def test_generate_plan_adds_xlsx_task_for_spreadsheet_objectives():
    _, tasks = generate_plan("Gerar planilha xlsx com resumo")

    assert any(task["title"] == "Gerar Relatório (xlsx)" for task in tasks)
    spreadsheet_task = next(task for task in tasks if task["title"] == "Gerar Relatório (xlsx)")
    assert spreadsheet_task["expected_output_format"] == "xlsx"
    assert "spreadsheet" in spreadsheet_task["required_tools"]


def test_dynamic_subtasks_are_bounded_by_depth_and_count():
    parent_task = {
        "task_id": "task-99",
        "title": "Implementar Solução",
        "depth": MAX_DECOMPOSITION_DEPTH,
    }

    assert (
        generate_dynamic_subtasks(
            parent_task,
            discoveries=["A", "B", "C"],
            max_depth=MAX_DECOMPOSITION_DEPTH,
        )
        == []
    )

    parent_task["depth"] = 0
    generated = generate_dynamic_subtasks(
        parent_task,
        discoveries=[f"Descoberta {idx}" for idx in range(10)],
        max_subtasks=MAX_SUBTASKS_PER_TASK,
    )
    assert len(generated) == MAX_SUBTASKS_PER_TASK
    assert all(task["parent_task_id"] == "task-99" for task in generated)
