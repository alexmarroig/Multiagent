from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langgraph_planner import generate_plan


def test_generate_plan_adds_core_tasks_in_order():
    plan_md, tasks = generate_plan("Melhorar API")

    assert "# Plano para: Melhorar API" in plan_md
    assert [task["order_index"] for task in tasks] == list(range(len(tasks)))
    assert [task["title"] for task in tasks[:3]] == [
        "Analisar Contexto",
        "Implementar Solução",
        "Validar Entrega",
    ]


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

    assert tasks[-1]["title"] == "Gerar Relatório (xlsx)"
