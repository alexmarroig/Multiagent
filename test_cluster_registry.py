from workers.cluster_registry import ClusterRegistry


def test_scheduler_uses_capability_and_load_for_routing():
    registry = ClusterRegistry()
    registry.register_worker(worker_id="w1", node_id="n1", capabilities={"gpu", "cpu"}, current_load=3)
    registry.register_worker(worker_id="w2", node_id="n2", capabilities={"cpu"}, current_load=1)

    assignment = registry.schedule_task(required_capability="cpu", priority=10)

    assert assignment is not None
    assert assignment.worker_id == "w2"


def test_scheduler_reserves_low_load_workers_for_high_priority_work():
    registry = ClusterRegistry(low_priority_cutoff=60, reserved_headroom=0.25)
    registry.register_worker(worker_id="reserved", node_id="n1", capabilities={"cpu"}, current_load=0.1)
    registry.register_worker(worker_id="busy", node_id="n2", capabilities={"cpu"}, current_load=0.5)

    low_priority_assignment = registry.schedule_task(required_capability="cpu", priority=90)
    high_priority_assignment = registry.schedule_task(required_capability="cpu", priority=5)

    assert low_priority_assignment is not None
    assert low_priority_assignment.worker_id == "busy"
    assert high_priority_assignment is not None
    assert high_priority_assignment.worker_id == "reserved"


def test_workers_can_join_and_leave_dynamically():
    registry = ClusterRegistry()
    assert registry.schedule_task(required_capability="gpu", priority=5) is None

    registry.register_worker(worker_id="w1", node_id="node-a", capabilities={"gpu"}, current_load=0)
    assignment = registry.schedule_task(required_capability="gpu", priority=5)
    assert assignment is not None
    assert assignment.worker_id == "w1"

    removed = registry.unregister_worker("w1")
    assert removed is True
    assert registry.schedule_task(required_capability="gpu", priority=5) is None
