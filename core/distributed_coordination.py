"""Distributed coordination for leader election and shard ownership."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from monitoring.runtime_metrics import runtime_metrics


@dataclass(slots=True)
class LeadershipState:
    node_id: str
    is_leader: bool
    lease_seconds: int


class RedisCoordinator:
    def __init__(self, redis_client: Any, *, namespace: str = "agentos:coord") -> None:
        self.redis = redis_client
        self.namespace = namespace

    def elect_leader(self, node_id: str, *, lease_seconds: int = 30) -> LeadershipState:
        key = f"{self.namespace}:leader"
        acquired = bool(self.redis.set(key, node_id, nx=True, ex=lease_seconds))
        if not acquired and self.redis.get(key) == node_id:
            self.redis.expire(key, lease_seconds)
            acquired = True
        if acquired:
            runtime_metrics.inc("coordination.leader_elections")
        return LeadershipState(node_id=node_id, is_leader=acquired, lease_seconds=lease_seconds)

    def claim_shard(self, shard_id: str, node_id: str, *, lease_seconds: int = 30) -> bool:
        key = f"{self.namespace}:shard:{shard_id}"
        claimed = bool(self.redis.set(key, node_id, nx=True, ex=lease_seconds))
        if claimed:
            runtime_metrics.inc("coordination.shards_claimed")
        return claimed

    def renew_shard(self, shard_id: str, node_id: str, *, lease_seconds: int = 30) -> bool:
        key = f"{self.namespace}:shard:{shard_id}"
        if self.redis.get(key) != node_id:
            return False
        self.redis.expire(key, lease_seconds)
        return True


class DuplicateExecutionGuard:
    def __init__(self, redis_client: Any, *, namespace: str = "agentos:dedupe") -> None:
        self.redis = redis_client
        self.namespace = namespace

    def acquire(self, task_id: str, *, ttl_seconds: int = 60 * 30) -> bool:
        return bool(self.redis.set(f"{self.namespace}:{task_id}", str(time.time()), nx=True, ex=ttl_seconds))
