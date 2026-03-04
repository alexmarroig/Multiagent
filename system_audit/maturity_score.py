from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class Check:
    description: str
    path: str


@dataclass(frozen=True)
class CategoryDefinition:
    checks: tuple[Check, ...]
    recommendation: str


CATEGORY_DEFINITIONS: dict[str, CategoryDefinition] = {
    "architecture": CategoryDefinition(
        checks=(
            Check("Core orchestration module exists", "core/orchestrator.py"),
            Check("Task graph engine exists", "tasks/task_graph_engine.py"),
            Check("Architecture audit documentation exists", "ARCHITECTURE_AUDIT.md"),
            Check("Executor app exists", "apps/executor/main.py"),
            Check("Orchestrator app exists", "apps/orchestrator/main.py"),
        ),
        recommendation="Strengthen system boundaries and update architecture docs with decision records.",
    ),
    "reliability": CategoryDefinition(
        checks=(
            Check("System reliability tests exist", "tests/reliability/test_system_reliability.py"),
            Check("Circuit breaker implementation exists", "backend/tools/circuit_breaker.py"),
            Check("Watchdog implementation exists", "workers/watchdog.py"),
            Check("Queue backpressure controller exists", "scheduler/queue_backpressure_controller.py"),
            Check("Reliability audit documentation exists", "PRODUCTION_RELIABILITY_AUDIT.md"),
        ),
        recommendation="Expand resilience testing with failure injection and measurable recovery objectives.",
    ),
    "security": CategoryDefinition(
        checks=(
            Check("JWT handler exists", "backend/auth/jwt_handler.py"),
            Check("Secret manager exists", "backend/auth/secret_manager.py"),
            Check("Authorization dependencies exist", "backend/auth/dependencies.py"),
            Check("Governance guardrails exist", "governance/guardrails.py"),
            Check("Governance approval service exists", "governance/human_approval_service.py"),
        ),
        recommendation="Increase defense-in-depth with security tests, threat modeling, and regular secret rotation automation.",
    ),
    "scalability": CategoryDefinition(
        checks=(
            Check("Agent autoscaler exists", "core/agent_autoscaler.py"),
            Check("Distributed queue exists", "core/task_queue.py"),
            Check("Adaptive scheduler exists", "scheduler/adaptive_scheduler.py"),
            Check("Load manager exists", "core/load_manager.py"),
            Check("Chaos or stress tests exist", "tests/chaos/test_resilience.py"),
        ),
        recommendation="Add load-test baselines and capacity plans for traffic tiers and burst scenarios.",
    ),
    "observability": CategoryDefinition(
        checks=(
            Check("Telemetry service exists", "monitoring/telemetry_service.py"),
            Check("Structured logging exists", "monitoring/structured_logging.py"),
            Check("Tracing module exists", "monitoring/tracing.py"),
            Check("Alerts module exists", "monitoring/alerts.py"),
            Check("SLO documentation exists", "backend/docs/observability/slo.md"),
        ),
        recommendation="Define end-to-end SLIs/SLOs and ensure dashboards and alert routing are continuously validated.",
    ),
    "governance": CategoryDefinition(
        checks=(
            Check("Policy engine exists", "governance/policy_engine.py"),
            Check("Approval queue exists", "governance/approval_queue.py"),
            Check("Control plane exists", "governance/control_plane.py"),
            Check("Human validation module exists", "governance/human_validation.py"),
            Check("Governance tests exist", "backend/tests/test_governance_approval_queue.py"),
        ),
        recommendation="Increase policy coverage and automate audits for high-risk actions and exception handling.",
    ),
    "testing": CategoryDefinition(
        checks=(
            Check("Root test suite includes context manager tests", "test_context_manager.py"),
            Check("Root test suite includes scheduler safety tests", "test_task_graph_engine_safety_limits.py"),
            Check("Backend test suite includes decomposer tests", "backend/tests/test_task_decomposer.py"),
            Check("API reliability tests exist", "tests/api/test_api_reliability.py"),
            Check("Pytest shared configuration exists", "tests/conftest.py"),
        ),
        recommendation="Improve quality gates with mutation/property tests and stricter CI coverage thresholds.",
    ),
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _score_category(category: CategoryDefinition, root: Path) -> tuple[int, list[str]]:
    passed = 0
    missing: list[str] = []
    for check in category.checks:
        if (root / check.path).exists():
            passed += 1
        else:
            missing.append(check.description)
    score = round((passed / len(category.checks)) * 100)
    return score, missing


def build_maturity_report() -> dict[str, object]:
    root = _repo_root()
    category_scores: dict[str, int] = {}
    recommendations: list[str] = []

    for name, definition in CATEGORY_DEFINITIONS.items():
        score, missing = _score_category(definition, root)
        category_scores[name] = score
        if score < 80:
            if missing:
                recommendations.append(
                    f"{name}: {definition.recommendation} Missing signals: {', '.join(missing)}."
                )
            else:
                recommendations.append(f"{name}: {definition.recommendation}")

    overall_score = round(sum(category_scores.values()) / len(category_scores))

    if not recommendations:
        recommendations.append(
            "All tracked categories are at or above target. Keep score freshness by rerunning this audit as the platform evolves."
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "category_scores": category_scores,
        "overall_score": overall_score,
        "recommendations": recommendations,
    }


def write_report(output_path: Path) -> Path:
    report = build_maturity_report()
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    root = _repo_root()
    output_file = root / "maturity_score.json"
    write_report(output_file)
    print(f"Wrote maturity score report to {output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
