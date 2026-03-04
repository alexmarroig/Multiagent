from __future__ import annotations

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend


def _execute_task(task_id: int, queue: DistributedTaskQueue) -> float:
    started = time.perf_counter()
    queue.enqueue_task({"task_id": f"stress-{task_id}", "name": "stress"})
    queue.dequeue_task(timeout_seconds=0)
    return time.perf_counter() - started


def run_stress_test(concurrency: int = 100, tasks: int = 500) -> dict[str, float]:
    queue = DistributedTaskQueue(InMemoryQueueBackend(), queue_high_watermark=200, queue_low_watermark=50)
    latencies: list[float] = []
    failures = 0

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(_execute_task, idx, queue) for idx in range(tasks)]
        for future in as_completed(futures):
            try:
                latencies.append(future.result())
            except Exception:
                failures += 1

    report = {
        "tasks": tasks,
        "concurrency": concurrency,
        "execution_latency_p50_ms": round(statistics.median(latencies) * 1000, 3) if latencies else 0.0,
        "execution_latency_p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] * 1000, 3) if latencies else 0.0,
        "failure_rate": round(failures / max(1, tasks), 4),
        "queue_depth": queue.queue_size(),
    }
    return report


if __name__ == "__main__":
    print(json.dumps(run_stress_test(), indent=2))
