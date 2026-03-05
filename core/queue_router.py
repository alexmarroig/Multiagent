"""Queue sharding router for tenant-aware horizontal scale."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.task_queue import DistributedTaskQueue, QueueTask
from security.tenant_context import enforce_context_in_metadata


@dataclass(slots=True)
class QueueShard:
    name: str
    weight: int = 1


class QueueShardRouter:
    def __init__(self, shard_queues: dict[str, DistributedTaskQueue], *, tenant_assignments: dict[str, str] | None = None) -> None:
        if not shard_queues:
            raise ValueError("at least one shard queue is required")
        self.shard_queues = shard_queues
        self.tenant_assignments = tenant_assignments or {}

    def list_shards(self) -> list[str]:
        return sorted(self.shard_queues)

    def assign_tenant(self, tenant_id: str, shard_name: str) -> None:
        if shard_name not in self.shard_queues:
            raise KeyError(f"unknown shard: {shard_name}")
        self.tenant_assignments[tenant_id] = shard_name

    def rebalance(self, shard_queues: dict[str, DistributedTaskQueue]) -> None:
        self.shard_queues = shard_queues
        for tenant, shard in list(self.tenant_assignments.items()):
            if shard not in self.shard_queues:
                self.tenant_assignments[tenant] = self._hash_shard(tenant)

    def scale_shards(self, shard_queues: dict[str, DistributedTaskQueue]) -> None:
        """Alias for dynamic shard topology updates."""
        self.rebalance(shard_queues)

    def worker_subscriptions(self) -> dict[str, DistributedTaskQueue]:
        """Expose shard queues for worker subscription bootstrapping."""
        return dict(self.shard_queues)

    def _hash_shard(self, tenant_id: str) -> str:
        shards = sorted(self.shard_queues)
        digest = int(hashlib.sha256(tenant_id.encode("utf-8")).hexdigest(), 16)
        return shards[digest % len(shards)]

    def shard_for_tenant(self, tenant_id: str) -> str:
        return self.tenant_assignments.get(tenant_id, self._hash_shard(tenant_id))

    def route_task(self, task: QueueTask) -> str:
        enforce_context_in_metadata(task.metadata, strict=False)
        tenant_id = str(task.metadata.get("tenant_id", "default"))
        shard_name = self.shard_for_tenant(tenant_id)
        task.metadata["queue_shard"] = shard_name
        self.shard_queues[shard_name].enqueue_task(task)
        return shard_name
