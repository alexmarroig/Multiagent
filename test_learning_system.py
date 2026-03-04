from agents.planner_agent import PlannerAgent
from learning.experience_store import ExperienceStore
from learning.performance_metrics import PerformanceMetrics
from learning.strategy_optimizer import StrategyOptimizer


def test_experience_store_records_required_learning_signals():
    store = ExperienceStore()

    store.record_task_outcome(task_id="t1", agent_id="a1", success=True, strategy_id="s1")
    store.record_execution_latency(task_id="t1", agent_id="a1", latency=1.7)
    store.record_tool_usage(task_id="t1", agent_id="a1", tool_name="pytest", success=True)
    store.record_error_rate(task_id="t1", agent_id="a1", has_error=False)

    kinds = [record.kind for record in store.all_records()]
    assert "task_outcome" in kinds
    assert "execution_latency" in kinds
    assert "tool_usage" in kinds
    assert "error_rate" in kinds


def test_strategy_optimizer_prioritizes_strategies_using_metrics():
    metrics = PerformanceMetrics()
    optimizer = StrategyOptimizer(metrics)

    metrics.record_execution(strategy_id="safe", success=True, latency=1.0, cost=1.0, tools=["pytest"]) 
    metrics.record_execution(strategy_id="safe", success=True, latency=1.2, cost=1.5, tools=["pytest"]) 
    metrics.record_execution(strategy_id="risky", success=False, latency=3.2, cost=2.8, tools=["custom"], error="failure")

    ranked = optimizer.prioritize_strategies(["risky", "safe"])

    assert ranked[0].strategy_id == "safe"
    assert ranked[0].success_rate > ranked[1].success_rate
    assert ranked[0].latency < ranked[1].latency


def test_planner_agent_loads_experience_before_plan_generation():
    store = ExperienceStore()
    store.record_task_outcome(task_id="t-history", agent_id="a1", success=True, strategy_id="s-best")

    metrics = PerformanceMetrics()
    metrics.record_execution(strategy_id="s-best", success=True, latency=0.8, cost=0.4, tools=["pytest"])
    metrics.record_execution(strategy_id="s-alt", success=False, latency=2.1, cost=1.1, tools=["custom"], error="boom")

    planner = PlannerAgent(experience_store=store, strategy_optimizer=StrategyOptimizer(metrics))
    plan = planner.create_plan(
        {
            "goal": "Improve API quality",
            "tasks": [
                {"task_id": "1", "strategy_id": "s-alt", "description": "Fallback strategy"},
                {"task_id": "2", "strategy_id": "s-best", "description": "Preferred strategy"},
            ],
        }
    )

    assert plan.objective["past_experiences"]
    assert plan.objective["strategy_scores"]
    assert plan.tasks[0]["strategy_id"] == "s-best"
