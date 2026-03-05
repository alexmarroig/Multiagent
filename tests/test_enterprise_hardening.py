from core.autoscaling_adapter import AutoscalingSignal, KEDAQueueAdapter, KubernetesHPAAdapter
from core.quota_ledger import DurableQuotaLedger, InMemoryQuotaStore, QuotaDebit, QuotaExceededError, QuotaPolicy
from core.queue_router import QueueShardRouter
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask


def test_quota_ledger_enforces_limits() -> None:
    ledger = DurableQuotaLedger(
        InMemoryQuotaStore(),
        policies={"t1": QuotaPolicy(tenant_token_quota=10, agent_token_quota=8, daily_cost_ceiling=1.0, monthly_cost_ceiling=5.0)},
    )
    ledger.debit(QuotaDebit(tenant_id="t1", agent_id="a1", request_id="r1", tokens=5, cost=0.5))
    try:
        ledger.debit(QuotaDebit(tenant_id="t1", agent_id="a1", request_id="r2", tokens=6, cost=0.1))
    except QuotaExceededError:
        pass
    else:
        raise AssertionError("quota should have been exceeded")


def test_queue_router_routes_to_assigned_shard() -> None:
    shards = {
        "task_queue_shard_A": DistributedTaskQueue(InMemoryQueueBackend(), queue_name="a"),
        "task_queue_shard_B": DistributedTaskQueue(InMemoryQueueBackend(), queue_name="b"),
        "task_queue_shard_C": DistributedTaskQueue(InMemoryQueueBackend(), queue_name="c"),
    }
    router = QueueShardRouter(shards)
    router.assign_tenant("tenant-x", "task_queue_shard_B")
    task = QueueTask(task_id="t1", name="n", metadata={"tenant_id": "tenant-x"})
    assert router.route_task(task) == "task_queue_shard_B"


def test_autoscaling_adapters_compute_replica_targets() -> None:
    signal = AutoscalingSignal(queue_depth=800, worker_utilization=0.9, p95_latency_ms=1200)
    assert KubernetesHPAAdapter().desired_replicas(signal) >= 2
    assert KEDAQueueAdapter().desired_replicas(signal) >= 2
