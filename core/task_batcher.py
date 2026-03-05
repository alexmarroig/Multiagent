"""Task batching primitives to amortize reasoning across similar tasks."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class BatchedTask:
    task_id: str
    task_type: str
    prompt: str
    payload: dict[str, Any] = field(default_factory=dict)


class TaskBatcher:
    """Groups tasks by signature, runs shared reasoning once, then fans out outputs."""

    def __init__(self, *, batch_size: int = 32) -> None:
        self.batch_size = max(1, batch_size)

    def group_similar_tasks(self, tasks: list[BatchedTask]) -> dict[str, list[BatchedTask]]:
        buckets: dict[str, list[BatchedTask]] = defaultdict(list)
        for task in tasks:
            signature = f"{task.task_type}:{task.prompt.strip().lower()}"
            buckets[signature].append(task)
        return dict(buckets)

    def execute_shared_reasoning(
        self,
        tasks: list[BatchedTask],
        reasoner: Callable[[str, list[BatchedTask]], dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        grouped = self.group_similar_tasks(tasks)
        outputs: dict[str, dict[str, Any]] = {}
        for signature, members in grouped.items():
            for index in range(0, len(members), self.batch_size):
                chunk = members[index : index + self.batch_size]
                shared = reasoner(signature, chunk)
                outputs.update(self.fan_out_results(chunk, shared))
        return outputs

    def fan_out_results(self, tasks: list[BatchedTask], shared_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
        fan_out: dict[str, dict[str, Any]] = {}
        for task in tasks:
            fan_out[task.task_id] = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "shared_reasoning": shared_result,
                "task_payload": task.payload,
            }
        return fan_out
