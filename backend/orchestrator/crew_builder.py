"""Builder de CrewAI a partir da configuração do canvas."""

from __future__ import annotations

import asyncio
import os
from collections import defaultdict, deque
from typing import Any

from crewai import Agent, Crew, Process, Task
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from models.schemas import AgentType, FlowConfig, LLMProvider, NodeConfig
from orchestrator.event_stream import make_event, publish_event
from tools.browser_tools import browse_website, search_hotels
from tools.calendar_tools import schedule_meeting
from tools.excel_tools import create_excel_spreadsheet
from tools.finance_tools import get_stock_data
from tools.phone_tools import make_phone_call
from tools.search_tools import web_search
from tools.tool_ids import normalize_tool_ids

DEFAULT_PROMPTS: dict[AgentType, str] = {
    AgentType.financial: "Analista financeiro sênior especializado em análise quantitativa e Excel",
    AgentType.travel: "Agente de viagens especialista em encontrar melhores ofertas e montar roteiros",
    AgentType.meeting: "Assistente executivo especializado em gestão de agenda corporativa",
    AgentType.phone: "Atendente profissional que realiza ligações com scripts precisos",
    AgentType.excel: "Especialista em Excel com domínio em fórmulas, gráficos e dashboards",
    AgentType.marketing: "Especialista em marketing digital, campanhas e análise de concorrência",
    AgentType.supervisor: "Supervisor que coordena agentes, delega tarefas e consolida resultados",
}

TOOL_REGISTRY = {
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
    event = make_event(session_id, agent_id, agent_name, event_type, content)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(publish_event(session_id, event))
        return

    loop.create_task(publish_event(session_id, event))


def _make_step_callback(session_id: str, node: NodeConfig):
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


def _make_task_callback(session_id: str, node: NodeConfig):
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
    original_execute_sync = task.execute_sync

    def execute_sync_with_hooks(agent=None, context=None, tools=None):
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="thinking",
            content=f"{node.label} iniciou a tarefa.",
        )
        try:
            return original_execute_sync(agent=agent, context=context, tools=tools)
        except Exception as exc:
            _publish_event_sync(
                session_id=session_id,
                agent_id=node.id,
                agent_name=node.label,
                event_type="error",
                content={"error": str(exc)},
            )
            raise

    task.execute_sync = execute_sync_with_hooks  # type: ignore[method-assign]


def _build_llm(provider: LLMProvider, model: str):
    if provider == LLMProvider.openai:
        return ChatOpenAI(model=model or os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"), temperature=0.2)
    if provider == LLMProvider.ollama:
        return ChatOllama(
            model=model or "llama3.1",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.2,
        )
    return ChatAnthropic(
        model=model or os.getenv("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022"),
        temperature=0.2,
    )


def _resolve_tools(tool_names: list[str]) -> list[Any]:
    tools: list[Any] = []
    normalized_tool_names, _ = normalize_tool_ids(tool_names)
    for name in normalized_tool_names:
        if name in TOOL_REGISTRY:
            tools.append(TOOL_REGISTRY[name])
    return tools


def topological_sort(nodes: list[NodeConfig], edges: list[tuple[str, str]]) -> list[NodeConfig]:
    node_map = {node.id: node for node in nodes}
    indegree: dict[str, int] = {node.id: 0 for node in nodes}
    graph: dict[str, list[str]] = defaultdict(list)

    for source, target in edges:
        graph[source].append(target)
        indegree[target] = indegree.get(target, 0) + 1

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
        raise ValueError("O fluxo contém ciclo ou nós inválidos.")

    return [node_map[nid] for nid in ordered_ids]


def build_crew_from_config(flow: FlowConfig) -> Crew:
    """Converte FlowConfig em CrewAI Crew sequencial."""
    ordered_nodes = topological_sort(flow.nodes, [(e.source, e.target) for e in flow.edges])

    predecessors: dict[str, list[str]] = defaultdict(list)
    for edge in flow.edges:
        predecessors[edge.target].append(edge.source)

    agent_by_id: dict[str, Agent] = {}
    task_by_id: dict[str, Task] = {}

    for node in ordered_nodes:
        prompt = node.system_prompt or DEFAULT_PROMPTS[node.agent_type]
        llm = _build_llm(node.provider, node.model)
        tools = _resolve_tools(node.tools)

        agent = Agent(
            role=node.label,
            goal=f"Executar tarefas do agente {node.label} com qualidade.",
            backstory=prompt,
            tools=tools,
            llm=llm,
            verbose=True,
            allow_delegation=node.agent_type == AgentType.supervisor,
            step_callback=_make_step_callback(flow.session_id, node),
        )
        agent_by_id[node.id] = agent

        pred_labels = [flow_node.label for flow_node in ordered_nodes if flow_node.id in predecessors[node.id]]
        ctx = f"Contexto anterior: {', '.join(pred_labels)}" if pred_labels else "Sem predecessores."
        task = Task(
            description=(
                f"Você é {node.label}. Execute sua etapa dentro do fluxo com base nos inputs: "
                f"{{inputs}}. {ctx}"
            ),
            expected_output=f"Saída estruturada e objetiva produzida por {node.label}.",
            agent=agent,
            callback=_make_task_callback(flow.session_id, node),
        )
        _wrap_task_execution(task, flow.session_id, node)
        task_by_id[node.id] = task

    tasks = [task_by_id[node.id] for node in ordered_nodes]
    agents = [agent_by_id[node.id] for node in ordered_nodes]

    return Crew(agents=agents, tasks=tasks, process=Process.sequential, memory=True, verbose=True)
