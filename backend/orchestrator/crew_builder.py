"""Builder de CrewAI a partir da configuração do canvas.

Responsabilidades:
- Resolver LLM por nó (OpenAI / Anthropic / Ollama)
- Resolver ferramentas por nó (com normalização)
- Ordenar grafo do fluxo (topological sort) e validar ciclos
- Criar Agents + Tasks com callbacks de streaming de eventos
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import time
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
TRANSIENT_ERROR_HINTS = (
    "timeout",
    "timed out",
    "tempor",
    "rate limit",
    "429",
    "connection",
    "unavailable",
    "503",
    "502",
    "reset by peer",
)


class ExecutionCancelledError(RuntimeError):
    """Sinaliza cancelamento cooperativo de execução."""

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
    event_recorder: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Publica um evento sem quebrar em contextos sync/thread.

    - Se houver loop rodando: agenda com create_task.
    - Se não houver loop: cria um loop temporário com asyncio.run.
    """
    event = make_event(session_id, agent_id, agent_name, event_type, content)
    if event_recorder is not None:
        event_recorder(event.model_dump(mode="json"))
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Sem loop ativo (ex.: thread do to_thread)
        asyncio.run(publish_event(session_id, event))
        return

    loop.create_task(publish_event(session_id, event))


def _is_transient_error(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in TRANSIENT_ERROR_HINTS)


def _extract_error_message(payload: Any) -> str | None:
    if isinstance(payload, dict) and payload.get("error"):
        return str(payload["error"])
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict) and parsed.get("error"):
            return str(parsed["error"])
        if payload.lower().startswith("erro"):
            return payload
    return None


def _make_step_callback(
    session_id: str,
    node: NodeConfig,
    event_recorder: Callable[[dict[str, Any]], None] | None,
) -> Callable[[Any], None]:
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
                "attempt": getattr(step, "attempt", 1),
                "duration_ms": getattr(step, "duration_ms", None),
                "tool_name": getattr(step, "tool", None),
            },
            event_recorder=event_recorder,
        )

    return _step_callback


def _make_task_callback(
    session_id: str,
    node: NodeConfig,
    event_recorder: Callable[[dict[str, Any]], None] | None,
) -> Callable[[Any], None]:
    """Callback no final da Task."""
    def _task_callback(output: Any) -> None:
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="result",
            content=getattr(output, "raw", str(output)),
            event_recorder=event_recorder,
        )

    return _task_callback


def _wrap_tool_with_retry(
    tool: Callable[..., Any],
    *,
    session_id: str,
    node: NodeConfig,
    max_attempts: int,
    base_delay_ms: int,
    event_recorder: Callable[[dict[str, Any]], None] | None,
) -> Callable[..., Any]:
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        for attempt in range(1, max(1, max_attempts) + 1):
            started = time.perf_counter()
            try:
                result = tool(*args, **kwargs)
                duration_ms = int((time.perf_counter() - started) * 1000)
                error_message = _extract_error_message(result)
                is_transient = bool(error_message and _is_transient_error(error_message))

                _publish_event_sync(
                    session_id=session_id,
                    agent_id=node.id,
                    agent_name=node.label,
                    event_type="tool_call",
                    content={
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "tool_name": getattr(tool, "__name__", str(tool)),
                        "status": "error" if error_message else "success",
                        "transient": is_transient,
                        "error": error_message,
                    },
                    event_recorder=event_recorder,
                )

                if error_message and is_transient and attempt < max_attempts:
                    time.sleep((base_delay_ms / 1000) * (2 ** (attempt - 1)))
                    continue

                return result
            except Exception as exc:  # noqa: BLE001
                duration_ms = int((time.perf_counter() - started) * 1000)
                transient = _is_transient_error(str(exc))
                _publish_event_sync(
                    session_id=session_id,
                    agent_id=node.id,
                    agent_name=node.label,
                    event_type="tool_call",
                    content={
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "tool_name": getattr(tool, "__name__", str(tool)),
                        "status": "error",
                        "transient": transient,
                        "error": str(exc),
                    },
                    event_recorder=event_recorder,
                )
                if not transient or attempt >= max_attempts:
                    raise
                time.sleep((base_delay_ms / 1000) * (2 ** (attempt - 1)))

        raise RuntimeError("Falha inesperada na execução da ferramenta.")

    return _wrapped


def _wrap_task_execution(
    task: Task,
    session_id: str,
    node: NodeConfig,
    *,
    timeout_seconds: int,
    max_attempts: int,
    base_delay_ms: int,
    event_recorder: Callable[[dict[str, Any]], None] | None,
    cancellation_checker: Callable[[], bool] | None,
) -> None:
    """Envolve execute_sync para publicar 'thinking' e 'error'."""
    original_execute_sync = task.execute_sync

    def execute_sync_with_hooks(*args: Any, **kwargs: Any) -> Any:
        _publish_event_sync(
            session_id=session_id,
            agent_id=node.id,
            agent_name=node.label,
            event_type="thinking",
            content=f"{node.label} iniciou a tarefa.",
            event_recorder=event_recorder,
        )
        if cancellation_checker and cancellation_checker():
            raise ExecutionCancelledError("Execução cancelada antes de iniciar a task.")

        for attempt in range(1, max(1, max_attempts) + 1):
            started = time.perf_counter()
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(original_execute_sync, *args, **kwargs)
                    output = future.result(timeout=timeout_seconds)

                duration_ms = int((time.perf_counter() - started) * 1000)
                _publish_event_sync(
                    session_id=session_id,
                    agent_id=node.id,
                    agent_name=node.label,
                    event_type="task_attempt",
                    content={
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "tool_name": None,
                        "status": "success",
                    },
                    event_recorder=event_recorder,
                )
                return output
            except concurrent.futures.TimeoutError as exc:
                duration_ms = int((time.perf_counter() - started) * 1000)
                message = f"Task excedeu timeout de {timeout_seconds}s"
                _publish_event_sync(
                    session_id=session_id,
                    agent_id=node.id,
                    agent_name=node.label,
                    event_type="task_attempt",
                    content={
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "tool_name": None,
                        "status": "error",
                        "transient": True,
                        "error": message,
                    },
                    event_recorder=event_recorder,
                )
                if attempt >= max_attempts:
                    raise TimeoutError(message) from exc
            except Exception as exc:  # noqa: BLE001
                duration_ms = int((time.perf_counter() - started) * 1000)
                transient = _is_transient_error(str(exc))
                _publish_event_sync(
                    session_id=session_id,
                    agent_id=node.id,
                    agent_name=node.label,
                    event_type="task_attempt",
                    content={
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "tool_name": None,
                        "status": "error",
                        "transient": transient,
                        "error": str(exc),
                    },
                    event_recorder=event_recorder,
                )
                if not transient or attempt >= max_attempts:
                    _publish_event_sync(
                        session_id=session_id,
                        agent_id=node.id,
                        agent_name=node.label,
                        event_type="error",
                        content={"error": str(exc), "transient": transient},
                        event_recorder=event_recorder,
                    )
                    raise

            if cancellation_checker and cancellation_checker():
                raise ExecutionCancelledError("Execução cancelada durante retentativa da task.")

            time.sleep((base_delay_ms / 1000) * (2 ** (attempt - 1)))

        raise RuntimeError("Task falhou sem retorno.")

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


def build_crew_from_config(
    flow: FlowConfig,
    *,
    event_recorder: Callable[[dict[str, Any]], None] | None = None,
    cancellation_checker: Callable[[], bool] | None = None,
) -> Crew:
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
        tools = [
            _wrap_tool_with_retry(
                tool,
                session_id=session_id,
                node=node,
                max_attempts=node.retry_max_attempts,
                base_delay_ms=node.retry_base_delay_ms,
                event_recorder=event_recorder,
            )
            for tool in _resolve_tools(node.tools)
        ]

        allow_delegation = node.agent_type == AgentType.supervisor

        agent = Agent(
            role=node.label,
            goal=f"Executar tarefas do agente {node.label} com qualidade.",
            backstory=prompt,
            tools=tools,
            llm=llm,
            verbose=True,
            allow_delegation=allow_delegation,
            step_callback=_make_step_callback(session_id, node, event_recorder),
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
            callback=_make_task_callback(session_id, node, event_recorder),
        )

        _wrap_task_execution(
            task,
            session_id,
            node,
            timeout_seconds=node.task_timeout_seconds,
            max_attempts=node.retry_max_attempts,
            base_delay_ms=node.retry_base_delay_ms,
            event_recorder=event_recorder,
            cancellation_checker=cancellation_checker,
        )
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
