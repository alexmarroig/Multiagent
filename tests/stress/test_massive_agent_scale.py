"""Stress simulation for massively scalable agent runtime primitives."""

from __future__ import annotations

import time

from core.agent_lifecycle_manager import AgentLifecycleManager, AgentState
from core.spawn_controller import SpawnController, SpawnLimits, SpawnRequest
from core.task_batcher import BatchedTask, TaskBatcher
from core.token_budget_scheduler import TokenBudgetConfig, TokenBudgetScheduler


def _simulate_scale(agent_count: int) -> dict[str, float]:
    spawn_controller = SpawnController(
        SpawnLimits(
            max_agents_global=max(6_000, agent_count + 100),
            max_agents_per_goal=max(6_000, agent_count + 100),
            max_spawn_per_minute=max(6_000, agent_count + 100),
            max_recursion_depth=4,
        )
    )
    lifecycle = AgentLifecycleManager(idle_timeout_seconds=5)
    scheduler = TokenBudgetScheduler(TokenBudgetConfig(global_budget=50_000_000, default_agent_budget=10_000, default_tenant_budget=40_000_000))

    queue_depth = 0
    started = time.perf_counter()
    for i in range(agent_count):
        goal_id = f"goal-{i % 20}"
        allowed = spawn_controller.request_spawn(
            SpawnRequest(goal_id=goal_id, parent_agent_id="coord-1", agent_type="worker", recursion_depth=1)
        )
        if not allowed:
            queue_depth += 1
            continue

        agent_id = f"agent-{i}"
        lifecycle.register(agent_id)
        lifecycle.transition(agent_id, AgentState.RUNNING)
        scheduler.record_usage(agent_id=agent_id, tenant_id="tenant-a", tokens=400)
        lifecycle.transition(agent_id, AgentState.COMPLETED)
        spawn_controller.complete_agent(goal_id)

    elapsed = max(time.perf_counter() - started, 1e-6)
    utilization = min(1.0, (agent_count - queue_depth) / max(agent_count, 1))
    return {
        "latency": elapsed,
        "queue_depth": float(queue_depth),
        "worker_utilization": utilization,
        "token_consumption": float(scheduler.snapshot()["global_used"]),
    }


def test_massive_agent_scale_stability() -> None:
    scenarios = [100, 1_000, 5_000]
    metrics = {size: _simulate_scale(size) for size in scenarios}

    assert metrics[100]["queue_depth"] == 0
    assert metrics[1_000]["worker_utilization"] > 0.95
    assert metrics[5_000]["worker_utilization"] > 0.90
    assert metrics[5_000]["latency"] < 3.0
    assert metrics[5_000]["token_consumption"] > metrics[1_000]["token_consumption"]


def test_batching_reduces_reasoning_calls() -> None:
    batcher = TaskBatcher(batch_size=64)
    tasks = [
        BatchedTask(task_id=f"r-{i}", task_type="research", prompt="market analysis", payload={"index": i})
        for i in range(10)
    ]
    calls = {"count": 0}

    def reasoner(signature: str, batch: list[BatchedTask]):
        calls["count"] += 1
        return {"signature": signature, "items": len(batch)}

    result = batcher.execute_shared_reasoning(tasks, reasoner)

    assert len(result) == 10
    assert calls["count"] == 1
