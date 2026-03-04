from scheduler.adaptive_scheduler import AdaptiveScheduler


def test_adjust_limits_reduces_spawn_and_pauses_low_priority_when_queue_is_high():
    scheduler = AdaptiveScheduler(
        queue_depth_threshold_high=5,
        queue_depth_threshold_critical=10,
        initial_task_spawn_rate=10,
    )

    state = scheduler.adjust_limits(queue_depth=6, worker_utilization=0.7, task_latency_ms=300)

    assert state["task_spawn_rate"] < 10
    assert state["low_priority_paused"] is True
    assert state["overload_protection_active"] is True


def test_adjust_limits_increases_parallelism_when_utilization_is_low():
    scheduler = AdaptiveScheduler(
        worker_utilization_threshold_low=0.4,
        initial_max_parallel_tasks=4,
        initial_worker_allocation=2,
        initial_task_spawn_rate=5,
    )

    state = scheduler.adjust_limits(queue_depth=0, worker_utilization=0.2, task_latency_ms=100)

    assert state["max_parallel_tasks"] > 4
    assert state["worker_allocation"] > 2
    assert state["task_spawn_rate"] > 5


def test_rank_candidates_filters_low_priority_tasks_during_overload():
    scheduler = AdaptiveScheduler(queue_depth_threshold_high=1, low_priority_cutoff=70)
    scheduler.adjust_limits(queue_depth=5, worker_utilization=0.8, task_latency_ms=100)

    ranked = scheduler.rank_candidates(
        graph_id="g-1",
        objective={
            "tasks": [
                {"task_id": "critical", "priority": 10},
                {"task_id": "normal", "priority": 50},
                {"task_id": "low", "priority": 80},
            ]
        },
    )

    ids = [task["task_id"] for task in ranked]
    assert ids == ["critical", "normal"]


def test_scheduler_recovers_and_unpauses_low_priority_after_pressure_drops():
    scheduler = AdaptiveScheduler(queue_depth_threshold_high=1)
    scheduler.adjust_limits(queue_depth=2, worker_utilization=0.8, task_latency_ms=100)

    state = scheduler.adjust_limits(queue_depth=0, worker_utilization=0.8, task_latency_ms=100)

    assert state["low_priority_paused"] is False
    assert state["overload_protection_active"] is False
