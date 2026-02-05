"""Utilities to transform a free-form objective into an execution plan.

This module keeps the planning logic deterministic and testable.  The goal is
not to replace a full LLM planner, but to provide a robust fallback that
produces useful tasks for common software quality and AI-ops objectives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PlanTemplate:
    """Represents a keyword-driven plan expansion."""

    keywords: tuple[str, ...]
    title: str
    description: str


# Ordered by priority: matching templates are appended in this order.
PLAN_TEMPLATES: tuple[PlanTemplate, ...] = (
    PlanTemplate(
        keywords=("refator", "reescre", "limpo", "leg", "eficiente"),
        title="Refatorar Código",
        description=(
            "Reestruturar o código para melhorar legibilidade, manutenção e "
            "clareza sem alterar o comportamento esperado."
        ),
    ),
    PlanTemplate(
        keywords=("erro", "corrig", "bug", "falha"),
        title="Diagnosticar e Corrigir Erros",
        description=(
            "Identificar causas raiz dos erros, aplicar correções e "
            "documentar o motivo técnico dos problemas encontrados."
        ),
    ),
    PlanTemplate(
        keywords=("teste", "pytest", "jest", "regress"),
        title="Criar e Automatizar Testes",
        description=(
            "Implementar testes unitários e regressivos automatizados para "
            "prevenir que mudanças futuras quebrem funcionalidades existentes."
        ),
    ),
    PlanTemplate(
        keywords=("desempenho", "performance", "escal", "gargalo", "carga"),
        title="Otimizar Desempenho e Escalabilidade",
        description=(
            "Analisar gargalos de execução e propor melhorias de performance "
            "com foco em escalabilidade."
        ),
    ),
    PlanTemplate(
        keywords=("anômal", "anomali", "monitor", "tempo real", "logs"),
        title="Monitoramento Inteligente e Anomalias",
        description=(
            "Implementar monitoramento contínuo, detecção de anomalias e "
            "análise de logs para diagnóstico proativo."
        ),
    ),
    PlanTemplate(
        keywords=("predit", "antecip", "prevent"),
        title="Modelos Preditivos de Falha",
        description=(
            "Desenvolver modelos preditivos para antecipar falhas potenciais "
            "e permitir ações preventivas."
        ),
    ),
    PlanTemplate(
        keywords=("seguran", "vulnerab"),
        title="Automatizar Testes de Segurança",
        description=(
            "Executar verificações automatizadas de segurança para identificar "
            "vulnerabilidades técnicas antes do deploy."
        ),
    ),
    PlanTemplate(
        keywords=("interface", "ui", "ux", "usabilidade", "compatibilidade"),
        title="Validar Interface e Compatibilidade",
        description=(
            "Automatizar testes de interface e compatibilidade para garantir "
            "consistência da experiência em diferentes plataformas."
        ),
    ),
    PlanTemplate(
        keywords=("pipeline", "ci", "integração contínua"),
        title="Integrar Qualidade ao Pipeline CI",
        description=(
            "Conectar verificações automatizadas ao pipeline de integração "
            "contínua para feedback rápido sobre mudanças."
        ),
    ),
)


BASE_TASKS: tuple[tuple[str, str], ...] = (
    (
        "Analisar Contexto",
        "Mapear requisitos, riscos técnicos e componentes afetados pelo objetivo.",
    ),
    (
        "Implementar Solução",
        "Executar alterações de código com foco em correção, clareza e confiabilidade.",
    ),
    (
        "Validar Entrega",
        "Executar verificações automáticas e preparar resumo técnico das mudanças.",
    ),
)


def _normalize(text: str) -> str:
    """Normalize user input for robust keyword matching."""

    return " ".join(text.lower().split())


def _matched_templates(objective: str) -> Iterable[PlanTemplate]:
    """Yield templates that match at least one keyword from objective."""

    normalized_objective = _normalize(objective)
    for template in PLAN_TEMPLATES:
        if any(keyword in normalized_objective for keyword in template.keywords):
            yield template


def _build_plan_markdown(objective: str, tasks: list[dict]) -> str:
    """Render the final markdown plan from selected tasks."""

    lines = [f"# Plano para: {objective}", "", "## Etapas propostas:"]
    for idx, task in enumerate(tasks, start=1):
        lines.append(f"{idx}. **{task['title']}** — {task['description']}")
    return "\n".join(lines)


def generate_plan(objective: str):
    """Generate markdown plan and ordered task payload for a given objective."""

    cleaned_objective = objective.strip()
    tasks: list[dict[str, str | int]] = []

    for title, description in BASE_TASKS:
        tasks.append({"title": title, "description": description})

    for template in _matched_templates(cleaned_objective):
        tasks.append({"title": template.title, "description": template.description})

    if "xlsx" in cleaned_objective.lower() or "planilha" in cleaned_objective.lower():
        tasks.append(
            {
                "title": "Gerar Relatório (xlsx)",
                "description": "Criar uma planilha de acompanhamento com métricas e resultados.",
            }
        )

    # Ensure stable order_index values after all dynamic expansions.
    for order_index, task in enumerate(tasks):
        task["order_index"] = order_index

    plan_markdown = _build_plan_markdown(cleaned_objective, tasks)
    return plan_markdown, tasks
