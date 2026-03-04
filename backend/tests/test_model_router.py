from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.model_router import select_model


def test_selects_small_fast_for_simple_classification() -> None:
    selected = select_model(
        {
            "task_type": "classification",
            "complexity": "simple",
            "latency_requirement": "high",
            "max_cost_tier": 2,
            "context_tokens": 512,
        }
    )

    assert selected == "gpt-4o-mini"


def test_selects_advanced_for_code_generation() -> None:
    selected = select_model(
        {
            "task_type": "code_generation",
            "complexity": "complex",
            "latency_requirement": "medium",
            "max_cost_tier": 3,
            "context_tokens": 4_096,
        }
    )

    assert selected == "claude-3-5-sonnet-20241022"


def test_selects_long_context_when_context_exceeds_small_model() -> None:
    selected = select_model(
        {
            "task_type": "analysis",
            "complexity": "medium",
            "latency_requirement": "low",
            "max_cost_tier": 4,
            "context_tokens": 180_000,
        }
    )

    assert selected == "claude-3-5-sonnet-20241022"


def test_budget_constraint_prefers_small_fast() -> None:
    selected = select_model(
        {
            "task_type": "analysis",
            "complexity": "complex",
            "latency_requirement": "medium",
            "max_cost_tier": 1,
            "context_tokens": 10_000,
        }
    )

    assert selected == "gpt-4o-mini"
