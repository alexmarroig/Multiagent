"""Builder de CrewAI a partir da configuração do canvas.

Responsabilidades:
- Resolver LLM por nó (OpenAI / Anthropic / Ollama)
- Resolver ferramentas por nó (com normalização)
- Ordenar grafo do fluxo (topological sort) e validar ciclos
- Criar Agents + Tasks com callbacks de streaming de eventos
"""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict, deque
from typing import Any, Callable, Iterable, Mapping

from crewai import Agent, Crew, Process, Task
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from models.schemas import AgentType, FlowConfig, LLMProvider, NodeConfig
from orchestrator.event_stream import make_event, publish_event
from tools.browser_tools import browse_website, search_hotels
from tools.calendar_tools import schedule_meeting
from tools.excel_tools import create_excel_spreadsheet
from tools.finance_tools import get_stock_data
from tools.phone_tools import make_phone_call
from tools.search_tools import web_search
from tools.tool_ids import normalize_tool_ids


DEFAULT_TEMPERATURE = 0.2

DEFAULT_PROMPTS: dict[AgentType, str] = {
    AgentType.financial: "Analista financeiro sênior especializado em análise quantitativa e Excel",
    AgentType.travel: "Agente de viagens especialista em encontrar melhores ofertas e montar roteiros",
    AgentType.meeting: "Assistente executivo especializado em gestão de agenda corporativa",
    AgentType.phone: "Atendente profissional que realiza ligações com scripts precisos",
    AgentType.excel: "Especialista em Excel com domínio em fórmulas, gráficos e dashboards",
    AgentType.marketing: "Especialista em marketing digital, campanhas e análise de concorrência",
    AgentType.supervisor: "Supervisor que coordena agentes, delega tarefas e consolida resultados",
}

# Observação: CrewAI costuma aceitar callables (tools) no Agent. Mantive esse padrão.
TOOL_REGISTRY: Mapping[str, Any] = {
    "excel": create_excel_spreadsheet,
    "phone": make_phone_call,
    "calendar": schedule_meeting,
    "search": web_search,
    "finance": get_stock_data,
    "browser": browse_website,
    "travel": search_hotels,
}


def _publish_event_sync(
    session_id: str,
    agent_id: str,
    agent_name: str,
    event_type: str,
    content: str | dict | list,
) -> None:
    """Publica um evento sem quebrar em contextos sync/thread.

    - Se houver loop rodando: agenda com create_task.
    - Se não houver loop: cria um loop temporário com asyncio.run.
    """
    event = make_event(session_id, agent_id, agent_name, event_type, content)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Sem loop ativo (ex.: thread do to_thread)
        asyncio.run(publish_event(session_id, event))
        return

    loop.create_task(publish_event(session_id, event))


def _make_step_callback(session_id: str, node: NodeConfig) -> Callable[[Any], None]:
    """Callback por step/tool-use. Mantém payload tolerante a diferentes shapes."""
    def _step_callback(step: Any) -> None:
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="tool_call",
            content={
                "tool": getattr(step, "tool", None),
                "tool_input": getattr(step, "tool_input", None),
                "thought": getattr(step, "thought", None),
                "result": getattr(step, "result", None),
            },
        )

    return _step_callback


def _make_task_callback(session_id: str, node: NodeConfig) -> Callable[[Any], None]:
    """Callback no final da Task."""
    def _task_callback(output: Any) -> None:
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="result",
            content=getattr(output, "raw", str(output)),
        )

    return _task_callback


def _wrap_task_execution(task: Task, session_id: str, node: NodeConfig) -> None:
    """Envolve execute_sync para publicar 'thinking' e 'error'."""
    original_execute_sync = task.execute_sync

    def execute_sync_with_hooks(*args: Any, **kwargs: Any) -> Any:
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="thinking",
            content=f"{node.label} iniciou a tarefa.",
        )
        try:
            return original_execute_sync(*args, **kwargs)
        except Exception as exc:
            _publish_event_sync(
                session_id=session_id,
                agent_id=node.id,
                agent_name=node.label,
                event_type="error",
                content={"error": str(exc)},
            )
            raise

    # monkey patch (CrewAI Task é classe externa)
    task.execute_sync = execute_sync_with_hooks  # type: ignore[method-assign]


def _build_llm(provider: LLMProvider, model: str | None):
    """Cria LLM (LangChain) com defaults por provider."""
    # Dica: deixe DEFAULT_LLM_MODEL para OpenAI/Anthropic separados, se quiser.
    if provider == LLMProvider.openai:
        chosen = model or os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=chosen, temperature=DEFAULT_TEMPERATURE)

    if provider == LLMProvider.ollama:
        chosen = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=chosen, base_url=base_url, temperature=DEFAULT_TEMPERATURE)

    # anthropic (default)
    chosen = model or os.getenv("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022")
    return ChatAnthropic(model=chosen, temperature=DEFAULT_TEMPERATURE)


def _resolve_tools(tool_names: Iterable[str]) -> list[Any]:
    """Normaliza e resolve nomes de ferramentas para callables.

    - Remove duplicatas mantendo ordem.
    - Ignora ferramentas desconhecidas (mas poderia lançar erro se você preferir).
    """
    normalized_tool_names, _meta = normalize_tool_ids(list(tool_names))

    resolved: list[Any] = []
    seen: set[str] = set()

    for name in normalized_tool_names:
        if name in seen:
            continue
        seen.add(name)

        tool = TOOL_REGISTRY.get(name)
        if tool is not None:
            resolved.append(tool)
        # Se quiser ser mais “estrito”, troque por: raise ValueError(...)
        # else: log/telemetria. Mantive silencioso para não quebrar fluxo.
    return resolved


def topological_sort(nodes: list[NodeConfig], edges: list[tuple[str, str]]) -> list[NodeConfig]:
    """Ordena nós por dependências (Kahn).

    Lança ValueError se houver ciclo ou referência inválida.
    """
    node_map = {node.id: node for node in nodes}
    indegree: dict[str, int] = {node.id: 0 for node in nodes}
    graph: dict[str, list[str]] = defaultdict(list)

    # valida referências
    for source, target in edges:
        if source not in node_map or target not in node_map:
            raise ValueError(f"Aresta inválida: {source} -> {target} (nó inexistente).")
        graph[source].append(target)
        indegree[target] += 1

    queue = deque([nid for nid, deg in indegree.items() if deg == 0])
    ordered_ids: list[str] = []

    while queue:
        nid = queue.popleft()
        ordered_ids.append(nid)
        for nxt in graph[nid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered_ids) != len(nodes):
        raise ValueError("O fluxo contém ciclo (ou dependências inconsistentes).")

    return [node_map[nid] for nid in ordered_ids]


def build_crew_from_config(flow: FlowConfig) -> Crew:
    """Converte FlowConfig em CrewAI Crew sequencial."""
    session_id = flow.session_id or "unknown-session"

    ordered_nodes = topological_sort(flow.nodes, [(e.source, e.target) for e in flow.edges])

    predecessors: dict[str, list[str]] = defaultdict(list)
    for edge in flow.edges:
        predecessors[edge.target].append(edge.source)

    agent_by_id: dict[str, Agent] = {}
    task_by_id: dict[str, Task] = {}

    # ajuda a montar labels de predecessores sem O(n^2) bobo
    label_by_id = {n.id: n.label for n in ordered_nodes}

    for node in ordered_nodes:
        prompt = node.system_prompt or DEFAULT_PROMPTS.get(node.agent_type, "")
        llm = _build_llm(node.provider, node.model)
        tools = _resolve_tools(node.tools)

        allow_delegation = node.agent_type == AgentType.supervisor

        agent = Agent(
            role=node.label,
            goal=f"Executar tarefas do agente {node.label} com qualidade.",
            backstory=prompt,
            tools=tools,
            llm=llm,
            verbose=True,
            allow_delegation=allow_delegation,
            step_callback=_make_step_callback(session_id, node),
        )
        agent_by_id[node.id] = agent

        pred_ids = predecessors.get(node.id, [])
        pred_labels = [label_by_id[p] for p in pred_ids if p in label_by_id]
        ctx = f"Contexto anterior: {', '.join(pred_labels)}" if pred_labels else "Sem predecessores."

        task = Task(
            description=(
                f"Você é {node.label}. Execute sua etapa dentro do fluxo com base nos inputs: "
                f"{{inputs}}. {ctx}"
            ),
            expected_output=f"Saída estruturada e objetiva produzida por {node.label}.",
            agent=agent,
            callback=_make_task_callback(session_id, node),
        )

        _wrap_task_execution(task, session_id, node)
        task_by_id[node.id] = task

    tasks = [task_by_id[n.id] for n in ordered_nodes]
    agents = [agent_by_id[n.id] for n in ordered_nodes]

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        memory=True,
        verbose=True,
    )
