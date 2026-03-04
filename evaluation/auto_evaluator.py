"""Automatic evaluator combining LLM-style critique and deterministic checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learning.experience_store import ExperienceStore


@dataclass(slots=True, frozen=True)
class EvaluationResult:
    llm_critique: str
    rule_validation_passed: bool
    goal_alignment_score: float
    overall_score: float


class AutoEvaluator:
    def __init__(self, *, experience_store: ExperienceStore) -> None:
        self.experience_store = experience_store

    def _llm_style_critique(self, goal: str, result: dict[str, Any]) -> str:
        status = "successful" if result.get("success") else "partially complete"
        missing = result.get("missing_requirements", [])
        if missing:
            return (
                f"Execution was {status}. Goal '{goal}' still misses requirements: "
                f"{', '.join(str(item) for item in missing)}."
            )
        return f"Execution was {status} and aligns with the stated goal '{goal}'."

    def _rule_based_validation(self, result: dict[str, Any]) -> bool:
        if result.get("error"):
            return False
        if "quality_checks" in result:
            return all(bool(item.get("passed", False)) for item in result["quality_checks"])
        return bool(result.get("success", True))

    def _goal_alignment_score(self, goal: str, result: dict[str, Any]) -> float:
        text = f"{result.get('summary', '')} {result.get('decision', '')}".lower()
        goal_tokens = {token for token in goal.lower().split() if len(token) > 3}
        if not goal_tokens:
            return 1.0 if result.get("success") else 0.0
        matched = sum(1 for token in goal_tokens if token in text)
        base = matched / len(goal_tokens)
        if result.get("success"):
            return min(1.0, base + 0.25)
        return base

    def evaluate(self, *, goal: str, result: dict[str, Any]) -> EvaluationResult:
        critique = self._llm_style_critique(goal, result)
        rules_passed = self._rule_based_validation(result)
        alignment = self._goal_alignment_score(goal, result)
        overall = (alignment + (1.0 if rules_passed else 0.0)) / 2.0

        evaluation = EvaluationResult(
            llm_critique=critique,
            rule_validation_passed=rules_passed,
            goal_alignment_score=alignment,
            overall_score=overall,
        )
        self.experience_store.store_evaluation(
            {
                "goal": goal,
                "result": result,
                "llm_critique": evaluation.llm_critique,
                "rule_validation_passed": evaluation.rule_validation_passed,
                "goal_alignment_score": evaluation.goal_alignment_score,
                "overall_score": evaluation.overall_score,
            }
        )
        return evaluation
