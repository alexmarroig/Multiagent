from scheduler.adaptive_scheduler import AdaptiveScheduler


def test_reduces_spawn_and_pauses_low_priority_when_queue_high():
    scheduler = AdaptiveScheduler(max_parallel_tasks=8, task_spawn_rate=2.0)

    state = scheduler.adjust_limits(queue_depth=150, worker_utilization=0.6, task_latency_ms=1000)

    assert state["low_priority_paused"] is True
    assert state["task_spawn_rate"] < 2.0

    ranked = scheduler.rank_candidates(
        graph_id="g1",
        objective={"tasks": [{"id": "lo", "priority": 80}, {"id": "hi", "priority": 10}]},
    )
    assert [task["id"] for task in ranked] == ["hi"]


def test_increases_parallelism_when_worker_utilization_low():
    scheduler = AdaptiveScheduler(max_parallel_tasks=4, worker_allocation=4)

    state = scheduler.adjust_limits(queue_depth=10, worker_utilization=0.2, task_latency_ms=500)

    assert state["max_parallel_tasks"] == 5
    assert state["worker_allocation"] == 5


def test_overload_protection_throttles_for_critical_pressure():
    scheduler = AdaptiveScheduler(max_parallel_tasks=10, worker_allocation=8, task_spawn_rate=3.0)

    state = scheduler.adjust_limits(queue_depth=300, worker_utilization=0.95, task_latency_ms=5000)

    assert state["overload_protection_active"] is True
    assert state["low_priority_paused"] is True
    assert state["max_parallel_tasks"] <= 8
    assert state["task_spawn_rate"] < 3.0
