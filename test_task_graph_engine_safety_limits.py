from agentos.communication.event_bus import EventBus
from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from agentos.governance.human_validation import HumanValidationController, HumanValidationError
from tasks.task_graph_engine import TaskGraphEngine, TaskGraphSafetyLimits


def test_blocks_when_max_total_tasks_exceeded_and_triggers_gate():
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    events = []
    bus = EventBus()
    bus.subscribe_event("task_graph.limit_exceeded", lambda event: events.append(event))
    validation = HumanValidationController()

    engine = TaskGraphEngine(
        queue,
        safety_limits=TaskGraphSafetyLimits(max_total_tasks=1, max_subtasks_per_task=5, max_task_depth=4, max_parallel_tasks=10),
        event_bus=bus,
        human_validation=validation,
    )

    engine.add_task(task_id="t1", name="root")

    try:
        engine.add_task(task_id="t2", name="overflow")
    except HumanValidationError:
        pass
    else:
        raise AssertionError("Expected human approval gate when max_total_tasks is exceeded")

    assert "t2" not in engine._tasks
    assert events
    assert events[0].payload["limit_name"] == "max_total_tasks"


def test_blocks_when_subtask_or_depth_limits_exceeded():
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    events = []
    bus = EventBus()
    bus.subscribe_event("task_graph.limit_exceeded", lambda event: events.append(event))
    validation = HumanValidationController()

    engine = TaskGraphEngine(
        queue,
        safety_limits=TaskGraphSafetyLimits(max_total_tasks=10, max_subtasks_per_task=1, max_task_depth=1, max_parallel_tasks=10),
        event_bus=bus,
        human_validation=validation,
    )

    engine.add_task(task_id="parent", name="parent")
    engine.mark_task_completed(
        "parent",
        spawned_tasks=[
            {"task_id": "child-1", "name": "child-1"},
        ],
    )

    try:
        engine.mark_task_completed(
            "child-1",
            spawned_tasks=[
                {"task_id": "grandchild", "name": "grandchild"},
            ],
        )
    except HumanValidationError:
        pass
    else:
        raise AssertionError("Expected human approval gate when max_task_depth is exceeded")

    assert "grandchild" not in engine._tasks
    assert any(event.payload["limit_name"] == "max_task_depth" for event in events)


def test_blocks_when_parallel_task_limit_exceeded():
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    events = []
    bus = EventBus()
    bus.subscribe_event("task_graph.limit_exceeded", lambda event: events.append(event))
    validation = HumanValidationController()

    engine = TaskGraphEngine(
        queue,
        safety_limits=TaskGraphSafetyLimits(max_total_tasks=10, max_subtasks_per_task=5, max_task_depth=4, max_parallel_tasks=1),
        event_bus=bus,
        human_validation=validation,
    )

    engine.add_task(task_id="first", name="first")

    try:
        engine.add_task(task_id="second", name="second")
    except HumanValidationError:
        pass
    else:
        raise AssertionError("Expected human approval gate when max_parallel_tasks is exceeded")

    assert "second" not in engine._tasks
    assert any(event.payload["limit_name"] == "max_parallel_tasks" for event in events)
