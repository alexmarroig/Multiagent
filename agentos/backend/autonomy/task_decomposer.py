"""Objective decomposition into bounded, context-safe hierarchical tasks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agentos.backend.orchestrator.task_queue import QueuedTask


@dataclass(slots=True)
class DecompositionConstraints:
    max_depth: int = 3
    max_subtasks_per_task: int = 4
    max_total_tasks: int = 24
    max_task_tokens: int = 220


class TaskDecomposer:
    """Breaks a high-level objective into a hierarchical queue of executable tasks."""

    def __init__(self, constraints: DecompositionConstraints | None = None) -> None:
        self.constraints = constraints or DecompositionConstraints()

    def decompose(self, *, objective: str, session_id: str, context: list[dict]) -> list[QueuedTask]:
        if not objective.strip():
            return []

        existing = {item.get("payload", {}).get("objective") for item in context}
        if objective in existing:
            return []

        tasks: list[QueuedTask] = []
        self._expand(
            task_text=objective,
            session_id=session_id,
            parent_task_id=None,
            depth=0,
            sequence=1,
            sink=tasks,
        )
        return tasks

    def generate_dynamic_subtasks(self, *, session_id: str, parent_task_id: str, discovered_work: list[dict]) -> list[QueuedTask]:
        generated: list[QueuedTask] = []
        for index, item in enumerate(discovered_work[: self.constraints.max_subtasks_per_task], start=1):
            description = str(item.get("description") or "Trabalho descoberto durante execução").strip()
            if not description:
                continue
            generated.append(
                QueuedTask(
                    task_id=item.get("task_id", f"{parent_task_id}-dyn-{index}"),
                    parent_task_id=parent_task_id,
                    agent_id=item.get("agent_id", "supervisor"),
                    description=description,
                    estimated_complexity=self._estimate_complexity(description, 0),
                    required_tools=self._required_tools(description),
                    expected_output_format=item.get("expected_output_format", self._output_format(description)),
                    payload={
                        **item.get("payload", {}),
                        "objective": description,
                        "parent_task_id": parent_task_id,
                        "depth": item.get("depth", 1),
                    },
                )
            )
        return generated

    def _expand(
        self,
        *,
        task_text: str,
        session_id: str,
        parent_task_id: str | None,
        depth: int,
        sequence: int,
        sink: list[QueuedTask],
    ) -> None:
        if len(sink) >= self.constraints.max_total_tasks:
            return

        task_id = f"{session_id}-t{len(sink) + 1}"
        complexity = self._estimate_complexity(task_text, depth)
        node = QueuedTask(
            task_id=task_id,
            parent_task_id=parent_task_id,
            agent_id="supervisor",
            description=task_text,
            estimated_complexity=complexity,
            required_tools=self._required_tools(task_text),
            expected_output_format=self._output_format(task_text),
            payload={
                "objective": task_text,
                "depth": depth,
                "sequence": sequence,
                "parent_task_id": parent_task_id,
                "estimated_tokens": self._estimate_tokens(task_text),
            },
        )
        sink.append(node)

        token_estimate = self._estimate_tokens(task_text)
        if depth >= self.constraints.max_depth or (complexity <= 2 and token_estimate <= self.constraints.max_task_tokens):
            return

        subtasks = self._split_task(task_text)
        for idx, sub in enumerate(subtasks[: self.constraints.max_subtasks_per_task], start=1):
            if len(sink) >= self.constraints.max_total_tasks:
                return
            self._expand(
                task_text=sub,
                session_id=session_id,
                parent_task_id=task_id,
                depth=depth + 1,
                sequence=idx,
                sink=sink,
            )

    def _split_task(self, objective: str) -> list[str]:
        chunks = [part.strip(" -") for part in re.split(r"\.|;|,|\be\b|\bthen\b|\bdepois\b", objective, flags=re.IGNORECASE)]
        chunks = [part for part in chunks if len(part.split()) >= 3]
        if chunks:
            return chunks

        words = objective.split()
        if len(words) < 12:
            return []

        pivot = max(4, min(len(words) - 4, len(words) // 2))
        return [" ".join(words[:pivot]), " ".join(words[pivot:])]

    def _estimate_complexity(self, text: str, depth: int) -> int:
        token_estimate = self._estimate_tokens(text)
        raw = 1 + token_estimate // 45 + max(0, 2 - depth)
        return min(5, max(1, raw))

    def _required_tools(self, text: str) -> list[str]:
        lower = text.lower()
        tools: list[str] = []
        if any(keyword in lower for keyword in ("api", "endpoint", "http", "serviço", "service")):
            tools.append("http_client")
        if any(keyword in lower for keyword in ("teste", "test", "valida", "assert")):
            tools.append("test_runner")
        if any(keyword in lower for keyword in ("document", "resumo", "report", "relatório", "markdown")):
            tools.append("docs_writer")
        if not tools:
            tools.append("general_llm")
        return tools

    def _output_format(self, text: str) -> str:
        lower = text.lower()
        if any(keyword in lower for keyword in ("json", "schema", "api")):
            return "json"
        if any(keyword in lower for keyword in ("relatório", "report", "markdown", "doc")):
            return "markdown"
        if any(keyword in lower for keyword in ("teste", "test")):
            return "test_report"
        return "text"

    def _estimate_tokens(self, text: str) -> int:
        return max(1, int(len(text.split()) * 1.5))
