from __future__ import annotations

from core.agent_admission_controller import AgentAdmissionController, AdmissionLimits, AgentStartRequest
from core.llm_request_governor import LLMGovernorLimits, LLMRequestGovernor
from core.planning_guard import PlanningGuard, PlanningGuardLimits
from core.swarm_stability_controller import SwarmStabilityController, SwarmStabilityThresholds


def test_spawn_burst_of_1000_agents_is_queued_and_stabilized() -> None:
    controller = AgentAdmissionController(
        AdmissionLimits(
            max_concurrent_agents=300,
            max_spawn_rate_per_tenant_per_minute=600,
            max_global_spawn_burst_per_10s=400,
        )
    )

    admitted = 0
    queued = 0
    for index in range(1000):
        allowed = controller.request_start(AgentStartRequest(agent_id=f"a-{index}", tenant_id=f"t-{index % 4}"))
        admitted += int(allowed)
        queued += int(not allowed)

    assert admitted == 300
    assert queued == 700
    assert controller.metrics()["queued_agent_starts"] == 700.0


def test_llm_failure_cascade_is_governed_by_limits() -> None:
    governor = LLMRequestGovernor(
        LLMGovernorLimits(
            max_requests_per_minute_per_agent=3,
            max_tokens_per_task=200,
            max_tokens_per_tenant_per_hour=500,
        )
    )

    assert governor.check_request(agent_id="agent-1", tenant_id="tenant-a", task_id="t1", tokens_requested=120) == (True, "allow")
    assert governor.check_request(agent_id="agent-1", tenant_id="tenant-a", task_id="t2", tokens_requested=120) == (
        True,
        "allow",
    )
    # Budget breach must reject, preventing token runaway.
    assert governor.check_request(agent_id="agent-2", tenant_id="tenant-a", task_id="t3", tokens_requested=300) == (
        False,
        "reject:max_tokens_per_task",
    )
    assert governor.check_request(agent_id="agent-2", tenant_id="tenant-a", task_id="t4", tokens_requested=3000) == (
        False,
        "reject:max_tokens_per_task",
    )


def test_queue_overload_detects_instability_and_pauses_spawns() -> None:
    stability = SwarmStabilityController(
        SwarmStabilityThresholds(max_agent_spawn_rate=20.0, max_queue_growth_rate=10.0, max_worker_saturation=0.8)
    )

    state = stability.evaluate(agent_spawn_rate=25.0, queue_growth_rate=12.0, worker_saturation=0.91)

    assert state["instability_detected"] is True
    assert state["pause_new_spawns"] is True
    assert state["prioritize_active_tasks"] is True


def test_planner_infinite_loop_is_terminated() -> None:
    guard = PlanningGuard(PlanningGuardLimits(max_loop_depth=5, max_repeated_plan_cycles=3, max_reflection_without_progress=2))

    decision = (True, None)
    for _ in range(10):
        decision = guard.record_cycle(agent_id="agent-loop", plan_signature="same-plan", made_progress=False)
        if not decision[0]:
            break

    assert decision[0] is False
    assert decision[1] in {"loop_depth_exceeded", "repeated_planning_cycle", "reflection_without_progress"}
