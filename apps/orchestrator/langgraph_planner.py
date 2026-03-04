"""Utilities to transform a free-form objective into an execution plan.

This module keeps the planning logic deterministic and testable.  The goal is
not to replace a full LLM planner, but to provide a robust fallback that
produces useful tasks for common software quality and AI-ops objectives.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from learning.experience_store import ExperienceStore
    from learning.performance_feedback import PerformanceFeedback


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

MAX_SUBTASKS_PER_TASK = 4
MAX_DECOMPOSITION_DEPTH = 2
MAX_DESCRIPTION_WORDS = 35


@dataclass(frozen=True)
class TaskNode:
    """Represents a decomposed task with explicit execution metadata."""

    task_id: str
    parent_task_id: str | None
    title: str
    description: str
    estimated_complexity: int
    required_tools: tuple[str, ...]
    expected_output_format: str
    depth: int


def _infer_required_tools(text: str) -> tuple[str, ...]:
    """Infer required tools from task context and objective language."""

    normalized = _normalize(text)
    tools: list[str] = ["planner"]
    if any(keyword in normalized for keyword in ("teste", "pytest", "jest", "regress")):
        tools.append("test_runner")
    if any(keyword in normalized for keyword in ("monitor", "anomali", "logs")):
        tools.append("observability")
    if any(keyword in normalized for keyword in ("pipeline", "ci", "integração contínua")):
        tools.append("ci")
    if any(keyword in normalized for keyword in ("planilha", "xlsx", "relatório")):
        tools.append("spreadsheet")
    if any(keyword in normalized for keyword in ("seguran", "vulnerab")):
        tools.append("security_scanner")
    return tuple(tools)


def _output_format_for_text(text: str) -> str:
    normalized = _normalize(text)
    if "xlsx" in normalized or "planilha" in normalized:
        return "xlsx"
    if any(keyword in normalized for keyword in ("teste", "pytest", "jest")):
        return "test-report"
    return "markdown"


def _estimate_complexity(description: str) -> int:
    """Return a lightweight 1..5 complexity estimate with context-size bias."""

    words = len(description.split())
    if words <= 12:
        return 1
    if words <= 20:
        return 2
    if words <= 30:
        return 3
    if words <= 45:
        return 4
    return 5


def _chunked_subtasks(description: str, max_subtasks: int) -> list[str]:
    """Break long descriptions into context-safe subtask chunks."""

    words = description.split()
    if len(words) <= MAX_DESCRIPTION_WORDS:
        return [description]

    chunk_size = max(8, math.ceil(len(words) / max_subtasks))
    chunks: list[str] = []
    for idx in range(0, len(words), chunk_size):
        chunk = " ".join(words[idx : idx + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
        if len(chunks) >= max_subtasks:
            break
    return chunks or [description]


def _node_to_payload(node: TaskNode, order_index: int) -> dict[str, str | int | None]:
    return {
        "task_id": node.task_id,
        "parent_task_id": node.parent_task_id,
        "title": node.title,
        "description": node.description,
        "estimated_complexity": node.estimated_complexity,
        "required_tools": list(node.required_tools),
        "expected_output_format": node.expected_output_format,
        "depth": node.depth,
        "order_index": order_index,
    }


def _decompose_tasks(
    objective: str,
    base_tasks: list[dict[str, str]],
    *,
    max_depth: int = MAX_DECOMPOSITION_DEPTH,
    max_subtasks: int = MAX_SUBTASKS_PER_TASK,
) -> list[TaskNode]:
    """Create a bounded hierarchical task tree from top-level tasks."""

    task_nodes: list[TaskNode] = []
    counter = 0

    def next_task_id() -> str:
        nonlocal counter
        counter += 1
        return f"task-{counter}"

    def add_node(title: str, description: str, parent_task_id: str | None, depth: int) -> TaskNode:
        node = TaskNode(
            task_id=next_task_id(),
            parent_task_id=parent_task_id,
            title=title,
            description=description,
            estimated_complexity=_estimate_complexity(description),
            required_tools=_infer_required_tools(f"{objective} {title} {description}"),
            expected_output_format=_output_format_for_text(f"{objective} {title} {description}"),
            depth=depth,
        )
        task_nodes.append(node)
        return node

    for task in base_tasks:
        root_node = add_node(task["title"], task["description"], parent_task_id=None, depth=0)
        if max_depth <= 0:
            continue

        chunks = _chunked_subtasks(task["description"], max_subtasks=max_subtasks)
        if len(chunks) == 1:
            continue

        for index, chunk in enumerate(chunks[:max_subtasks], start=1):
            add_node(
                title=f"{task['title']} · Subtarefa {index}",
                description=chunk,
                parent_task_id=root_node.task_id,
                depth=1,
            )

    return task_nodes


def generate_dynamic_subtasks(
    parent_task: dict[str, str | int | None],
    discoveries: list[str],
    *,
    max_depth: int = MAX_DECOMPOSITION_DEPTH,
    max_subtasks: int = MAX_SUBTASKS_PER_TASK,
) -> list[dict[str, str | int | None]]:
    """Create bounded dynamic subtasks when execution uncovers new work."""

    current_depth = int(parent_task.get("depth", 0))
    if current_depth >= max_depth:
        return []

    parent_task_id = str(parent_task["task_id"])
    generated: list[dict[str, str | int | None]] = []
    for idx, discovery in enumerate(discoveries[:max_subtasks], start=1):
        task_id = f"{parent_task_id}.d{idx}"
        composed_text = f"{parent_task.get('title', '')} {discovery}".strip()
        generated.append(
            {
                "task_id": task_id,
                "parent_task_id": parent_task_id,
                "title": f"Investigar descoberta {idx}",
                "description": discovery,
                "estimated_complexity": _estimate_complexity(discovery),
                "required_tools": list(_infer_required_tools(composed_text)),
                "expected_output_format": _output_format_for_text(composed_text),
                "depth": current_depth + 1,
                "order_index": idx - 1,
            }
        )

    return generated


def _normalize(text: str) -> str:
    """Normalize user input for robust keyword matching."""

    return " ".join(text.lower().split())


def _matched_templates(objective: str) -> Iterable[PlanTemplate]:
    """Yield templates that match at least one keyword from objective."""

    normalized_objective = _normalize(objective)
    for template in PLAN_TEMPLATES:
        if any(keyword in normalized_objective for keyword in template.keywords):
            yield template


def _build_plan_markdown(
    objective: str,
    tasks: list[dict],
    planning_context: list[str] | None = None,
) -> str:
    """Render the final markdown plan from selected tasks."""

    lines = [f"# Plano para: {objective}", "", "## Etapas propostas:"]
    if planning_context:
        lines.extend(["", "## Contexto adaptativo considerado:"])
        for item in planning_context:
            lines.append(f"- {item}")
    for idx, task in enumerate(tasks, start=1):
        lines.append(
            f"{idx}. **{task['title']}** — {task['description']} "
            f"(id={task['task_id']}, parent={task['parent_task_id']}, "
            f"complexidade={task['estimated_complexity']}, "
            f"ferramentas={', '.join(task['required_tools'])}, "
            f"formato={task['expected_output_format']})"
        )
    return "\n".join(lines)


def generate_plan(
    objective: str,
    experience_store: "ExperienceStore | None" = None,
    performance_feedback: "PerformanceFeedback | None" = None,
):
    """Generate markdown plan and ordered task payload for a given objective."""

    cleaned_objective = objective.strip()
    tasks: list[dict[str, str | int]] = []
    planning_context: list[str] = []

    if experience_store is not None:
        similar_records = experience_store.query_similar(
            cleaned_objective,
            limit=3,
            kinds={"task_outcome", "success_metrics", "execution_trace", "evaluation"},
        )
        for record in similar_records:
            summary = record.payload.get("task_id") or record.payload.get("goal") or record.kind
            planning_context.append(f"Histórico similar: {summary}")

    if performance_feedback is not None:
        signals = performance_feedback.planner_signals()
        planning_context.append(
            "Taxa de sucesso histórica: "
            f"{signals['global_success_rate']:.0%}; falhas repetidas={signals['repeated_failures']}"
        )

        tool_effectiveness = signals.get("tool_effectiveness", {})
        if tool_effectiveness:
            best_tool, best_score = max(tool_effectiveness.items(), key=lambda item: item[1])
            planning_context.append(f"Ferramenta mais efetiva: {best_tool} ({best_score:.0%})")

        agent_history = signals.get("agent_performance", {})
        if agent_history:
            best_agent, perf = max(agent_history.items(), key=lambda item: item[1]["success_rate"])
            planning_context.append(
                f"Agente com melhor histórico: {best_agent} "
                f"({perf['success_rate']:.0%} sucesso)"
            )

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

    decomposed = _decompose_tasks(cleaned_objective, tasks)
    task_payloads = [_node_to_payload(node, order_index=i) for i, node in enumerate(decomposed)]

    plan_markdown = _build_plan_markdown(cleaned_objective, task_payloads, planning_context)
    return plan_markdown, task_payloads
