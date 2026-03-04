"""Policy-based model router for task-specific LLM selection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class TaskComplexity(str, Enum):
    simple = "simple"
    medium = "medium"
    complex = "complex"


class LatencyRequirement(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskType(str, Enum):
    classification = "classification"
    extraction = "extraction"
    summarization = "summarization"
    qa = "qa"
    code_generation = "code_generation"
    planning = "planning"
    analysis = "analysis"
    general = "general"


@dataclass(frozen=True)
class ModelProfile:
    name: str
    max_context_tokens: int
    relative_cost: int
    relative_latency: int


MODEL_CATALOG: dict[str, ModelProfile] = {
    "small_fast": ModelProfile(
        name="gpt-4o-mini",
        max_context_tokens=128_000,
        relative_cost=1,
        relative_latency=1,
    ),
    "advanced": ModelProfile(
        name="claude-3-5-sonnet-20241022",
        max_context_tokens=200_000,
        relative_cost=3,
        relative_latency=2,
    ),
    "long_context": ModelProfile(
        name="claude-3-5-sonnet-20241022",
        max_context_tokens=200_000,
        relative_cost=3,
        relative_latency=2,
    ),
    "budget": ModelProfile(
        name="gpt-4o-mini",
        max_context_tokens=128_000,
        relative_cost=1,
        relative_latency=1,
    ),
}


def _normalize_enum(value: Any, enum_type: type[Enum], default: Enum) -> Enum:
    if isinstance(value, enum_type):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        for item in enum_type:
            if item.value == normalized:
                return item

    return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def select_model(task_metadata: Mapping[str, Any]) -> str:
    """Select a model name based on task metadata.

    Expected metadata keys (all optional):
      - task_type: one of TaskType values
      - complexity: simple|medium|complex
      - latency_requirement: high|medium|low (high means lower latency needed)
      - max_cost_tier: integer budget tier from 1 (strict) to 5 (flexible)
      - context_tokens: estimated context window needed
    """

    task_type = _normalize_enum(task_metadata.get("task_type"), TaskType, TaskType.general)
    complexity = _normalize_enum(task_metadata.get("complexity"), TaskComplexity, TaskComplexity.medium)
    latency = _normalize_enum(
        task_metadata.get("latency_requirement"),
        LatencyRequirement,
        LatencyRequirement.medium,
    )

    max_cost_tier = _as_int(task_metadata.get("max_cost_tier"), default=3)
    context_tokens = _as_int(task_metadata.get("context_tokens"), default=0)

    # 1) Long-context needs win first.
    if context_tokens > MODEL_CATALOG["small_fast"].max_context_tokens:
        return MODEL_CATALOG["long_context"].name

    # 2) Task-specific overrides.
    if task_type == TaskType.classification and complexity == TaskComplexity.simple:
        return MODEL_CATALOG["small_fast"].name

    if task_type == TaskType.code_generation:
        if max_cost_tier <= 1 and latency == LatencyRequirement.high:
            return MODEL_CATALOG["small_fast"].name
        return MODEL_CATALOG["advanced"].name

    # 3) Multi-factor policy.
    if max_cost_tier <= 1:
        return MODEL_CATALOG["budget"].name

    if latency == LatencyRequirement.high and complexity == TaskComplexity.simple:
        return MODEL_CATALOG["small_fast"].name

    if complexity == TaskComplexity.complex:
        return MODEL_CATALOG["advanced"].name

    return MODEL_CATALOG["small_fast"].name
