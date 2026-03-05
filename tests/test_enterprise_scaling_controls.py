from __future__ import annotations

import pytest

from core.agent_admission_controller import AdmissionLimits, AgentAdmissionController, AgentStartRequest
from core.model_gateway import ModelGateway, ModelRequest
from core.quota_ledger import DurableQuotaLedger, InMemoryQuotaStore, QuotaPolicy
from core.queue_router import QueueShardRouter
from core.semantic_cache import SemanticLLMCache
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask
from security.tenant_context import TenantContext


def test_admission_controller_enforces_per_tenant_active_cap() -> None:
    controller = AgentAdmissionController(
        AdmissionLimits(
            max_concurrent_agents=100,
            max_spawn_rate_per_tenant_per_minute=100,
            max_global_spawn_burst_per_10s=100,
            max_active_agents_per_tenant=2,
        )
    )
    assert controller.request_start(AgentStartRequest(agent_id="a1", tenant_id="tenant-a"))
    assert controller.request_start(AgentStartRequest(agent_id="a2", tenant_id="tenant-a"))
    assert not controller.request_start(AgentStartRequest(agent_id="a3", tenant_id="tenant-a"))


def test_semantic_cache_is_tenant_and_model_isolated() -> None:
    cache = SemanticLLMCache(similarity_threshold=0.8)
    cache.store("Revenue summary", "tenant-a-fast", tenant_id="tenant-a", model="fast")
    assert cache.lookup("Revenue summary", tenant_id="tenant-a", model="fast") == "tenant-a-fast"
    assert cache.lookup("Revenue summary", tenant_id="tenant-b", model="fast") is None
    assert cache.lookup("Revenue summary", tenant_id="tenant-a", model="reasoning") is None


def test_queue_router_moves_unassigned_tenant_to_least_loaded_shard_under_pressure() -> None:
    shard_a = DistributedTaskQueue(InMemoryQueueBackend(), queue_name="a", queue_high_watermark=1, queue_low_watermark=0)
    shard_b = DistributedTaskQueue(InMemoryQueueBackend(), queue_name="b", queue_high_watermark=10, queue_low_watermark=3)
    shard_a.enqueue_task(QueueTask(task_id="seed", name="seed", metadata={"tenant_id": "seed"}))
    router = QueueShardRouter({"shard-a": shard_a, "shard-b": shard_b})

    task = QueueTask(task_id="task-1", name="n", metadata={"tenant_id": "tenant-z"})
    routed = router.route_task(task)
    assert routed == "shard-b"


def test_model_gateway_enforces_allowlist_and_uses_semantic_cache() -> None:
    ledger = DurableQuotaLedger(
        InMemoryQuotaStore(),
        policies={"tenant-a": QuotaPolicy(tenant_token_quota=1000, agent_token_quota=1000, daily_cost_ceiling=100, monthly_cost_ceiling=500)},
    )
    gateway = ModelGateway(
        quota_ledger=ledger,
        model_router={"fast": lambda req: f"answer:{req.prompt}"},
        tenant_model_allowlist={"tenant-a": {"fast"}},
        semantic_cache=SemanticLLMCache(similarity_threshold=0.99),
    )
    ctx = TenantContext(tenant_id="tenant-a", agent_id="agent-1", request_id="req-1")

    first = gateway.call(
        ModelRequest(prompt="hello", model="fast", max_tokens=100, estimated_tokens=10, estimated_cost=0.1, metadata={}),
        context=ctx,
    )
    second = gateway.call(
        ModelRequest(prompt="hello", model="fast", max_tokens=100, estimated_tokens=10, estimated_cost=0.1, metadata={}),
        context=ctx,
    )
    assert first["output"] == "answer:hello"
    assert second["usage"]["cached"] is True

    with pytest.raises(PermissionError):
        gateway.call(
            ModelRequest(prompt="blocked", model="reasoning", max_tokens=100, estimated_tokens=10, estimated_cost=0.1, metadata={}),
            context=ctx,
        )
