"""Infrastructure autoscaling adapters for Kubernetes HPA and KEDA."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AutoscalingSignal:
    queue_depth: int
    worker_utilization: float
    p95_latency_ms: float


class KubernetesHPAAdapter:
    def desired_replicas(self, signal: AutoscalingSignal, *, min_replicas: int = 1, max_replicas: int = 200) -> int:
        pressure = max(signal.queue_depth / 100.0, signal.worker_utilization, signal.p95_latency_ms / 1500.0)
        replicas = int(round(min_replicas + pressure * 10))
        return max(min_replicas, min(max_replicas, replicas))


class KEDAQueueAdapter:
    def desired_replicas(self, signal: AutoscalingSignal, *, target_queue_per_replica: int = 25, min_replicas: int = 1, max_replicas: int = 500) -> int:
        by_queue = max(min_replicas, (signal.queue_depth + target_queue_per_replica - 1) // target_queue_per_replica)
        by_latency = int(max(1, round(signal.p95_latency_ms / 250.0)))
        return max(min_replicas, min(max_replicas, max(by_queue, by_latency)))
