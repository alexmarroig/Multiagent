"""Builder de CrewAI a partir da configuração do canvas."""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
import time
from collections import defaultdict
from typing import Any, Callable, Iterable, Mapping

from crewai import Agent, Crew, Process, Task
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from models.schemas import AgentType, FlowConfig, LLMProvider, NodeConfig
from observability.logging import log_structured
from observability.metrics import metrics_store
from orchestrator.event_stream import make_event, publish_event
from tools.tool_ids import normalize_tool_ids


logger = logging.getLogger("agentos-orchestrator")


DEFAULT_TEMPERATURE = 0.2


class ExecutionCancelledError(RuntimeError):
    pass


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
)


DEFAULT_PROMPTS: dict[AgentType, str] = {
    AgentType.supervisor: "Supervisor que coordena agentes e consolida resultados",
}


def _is_transient_error(message: str) -> bool:
    return any(hint in message.lower() for hint in TRANSIENT_ERROR_HINTS)


def _build_llm(provider: LLMProvider, model: str | None):
    if provider == LLMProvider.openai:
        chosen = model or os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=chosen, temperature=DEFAULT_TEMPERATURE)

    if provider == LLMProvider.ollama:
        chosen = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=chosen, base_url=base_url, temperature=DEFAULT_TEMPERATURE)

    chosen = model or os.getenv("DEFAULT_LLM_MODEL", "claude-3-5-sonnet-20241022")
    return ChatAnthropic(model=chosen, temperature=DEFAULT_TEMPERATURE)


def _publish_event_sync(
    session_id: str,
    agent_id: str,
    agent_name: str,
    event_type: str,
    content: Any,
    event_recorder: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    event = make_event(session_id, agent_id, agent_name, event_type, content)
    if event_recorder:
        event_recorder(event.model_dump(mode="json"))

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(publish_event(session_id, event))
    except RuntimeError:
        asyncio.run(publish_event(session_id, event))


def _make_step_callback(
    session_id: str,
    node: NodeConfig,
    event_recorder: Callable[[dict[str, Any]], None] | None,
) -> Callable[[Any], None]:
    def callback(step: Any) -> None:
        _publish_event_sync(
            session_id,
            node.id,
            node.label,
            "tool_call",
            {
                "tool": getattr(step, "tool", None),
                "result": getattr(step, "result", None),
            },
            event_recorder,
        )

    return callback


def _make_task_callback(
    session_id: str,
    node: NodeConfig,
    event_recorder: Callable[[dict[str, Any]], None] | None,
):
    def callback(output: Any) -> None:
        _publish_event_sync(
            session_id,
            node.id,
            node.label,
            "result",
            getattr(output, "raw", str(output)),
            event_recorder,
        )

    return callback


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
    original = task.execute_sync

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if cancellation_checker and cancellation_checker():
            raise ExecutionCancelledError("Execução cancelada.")

        for attempt in range(1, max(1, max_attempts) + 1):
            started = time.perf_counter()
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(original, *args, **kwargs)
                    result = future.result(timeout=timeout_seconds)

                return result

            except Exception as exc:
                transient = _is_transient_error(str(exc))
                _publish_event_sync(
                    session_id,
                    node.id,
                    node.label,
                    "task_error",
                    {"error": str(exc), "transient": transient},
                    event_recorder,
                )

                if not transient or attempt >= max_attempts:
                    raise

                time.sleep((base_delay_ms / 1000) * (2 ** (attempt - 1)))

        raise RuntimeError("Falha na task")

    task.execute_sync = wrapped  # type: ignore


def _resolve_tools(tool_names: Iterable[str]) -> list[Any]:
    normalized, _ = normalize_tool_ids(list(tool_names))
    return []  # ferramentas externas são resolvidas em outra camada


def topological_sort(nodes: list[NodeConfig], edges: list[tuple[str, str]]) -> list[NodeConfig]:
    node_map = {node.id: node for node in nodes}
    indegree = {node.id: 0 for node in nodes}
    graph: dict[str, list[str]] = defaultdict(list)

    for source, target in edges:
        graph[source].append(target)
        indegree[target] += 1

    ready = [nid for nid, deg in indegree.items() if deg == 0]
    ordered: list[str] = []

    while ready:
        nid = ready.pop()
        ordered.append(nid)
        for nxt in graph[nid]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)

    if len(ordered) != len(nodes):
        raise ValueError("Fluxo contém ciclo.")

    return [node_map[nid] for nid in ordered]


def build_crew_from_config(
    flow: FlowConfig,
    *,
    event_recorder: Callable[[dict[str, Any]], None] | None = None,
    cancellation_checker: Callable[[], bool] | None = None,
) -> Crew:
    session_id = flow.session_id or "unknown-session"

    ordered_nodes = topological_sort(
        flow.nodes,
        [(e.source, e.target) for e in flow.edges],
    )

    agents: list[Agent] = []
    tasks: list[Task] = []

    for node in ordered_nodes:
        prompt = node.system_prompt or DEFAULT_PROMPTS.get(node.agent_type, "")
        llm = _build_llm(node.provider, node.model)

        agent = Agent(
            role=node.label,
            goal=f"Executar tarefas do agente {node.label}",
            backstory=prompt,
            tools=[],
            llm=llm,
            verbose=True,
            allow_delegation=node.agent_type == AgentType.supervisor,
            step_callback=_make_step_callback(session_id, node, event_recorder),
        )

        task = Task(
            description=f"Execute sua etapa com base nos inputs: {{inputs}}",
            expected_output=f"Saída de {node.label}",
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

        agents.append(agent)
        tasks.append(task)

    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        memory=True,
        verbose=True,
    )
