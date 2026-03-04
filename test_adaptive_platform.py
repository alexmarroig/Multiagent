from learning.experience_store import ExperienceStore
from learning.performance_feedback import PerformanceFeedback
from apps.orchestrator.langgraph_planner import generate_plan
from evaluation.auto_evaluator import AutoEvaluator
from governance.human_validation import HumanValidationController, HumanValidationError, ValidationGates
from governance.policy_engine import Policy, PolicyEngine, PolicyViolationError
from monitoring.alerts import AlertManager


def test_planner_uses_experience_and_feedback_context():
    store = ExperienceStore()
    feedback = PerformanceFeedback()
    store.store_task_outcome("t-1", {"success": True, "summary": "improve API reliability"})
    feedback.record_execution({"success": True, "execution_time": 1.2, "cost": 0.5, "tool": "pytest", "agent_id": "a1"})

    plan_md, _ = generate_plan("Melhorar API reliability", experience_store=store, performance_feedback=feedback)

    assert "Contexto adaptativo considerado" in plan_md
    assert "Taxa de sucesso histórica" in plan_md


def test_auto_evaluator_writes_to_experience_store():
    store = ExperienceStore()
    evaluator = AutoEvaluator(experience_store=store)

    result = evaluator.evaluate(goal="Ship regression tests", result={"success": True, "summary": "Added regression tests"})

    assert result.overall_score > 0
    assert any(record.kind == "evaluation" for record in store.all_records())


def test_human_validation_and_policy_controls():
    validation = HumanValidationController(
        ValidationGates(require_pre_execution_approval=True, require_high_cost_approval=True, high_cost_threshold=10)
    )

    try:
        validation.validate_task(task_id="1", payload={"estimated_cost": 15})
    except HumanValidationError:
        pass
    else:
        raise AssertionError("Expected human validation gate to pause execution")

    validation.grant_approval("task:1:execute")
    validation.grant_approval("task:1:cost")
    validation.validate_task(task_id="1", payload={"estimated_cost": 15})

    policy_engine = PolicyEngine(Policy(max_cost=20, max_risk_level="medium", restricted_tools={"danger_tool"}))

    try:
        policy_engine.enforce({"tool": "danger_tool", "estimated_cost": 5, "risk_level": "low"})
    except PolicyViolationError:
        pass
    else:
        raise AssertionError("Expected tool restriction policy violation")


def test_alert_manager_emits_failure_and_policy_alerts():
    manager = AlertManager(failure_threshold=2)
    manager.observe_result({"task_id": "1", "success": False, "cost": 1})
    alerts = manager.observe_result({"task_id": "2", "success": False, "cost": 1, "policy_violation": "risk_limit_exceeded"})

    categories = {alert.category for alert in alerts}
    assert "failure_threshold" in categories
    assert "policy_violation" in categories
