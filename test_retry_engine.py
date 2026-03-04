from __future__ import annotations

from communication.event_bus import EventBus
from core.execution_gateway import ExecutionGateway, GatewayPolicy
from core.retry_engine import RetryEngine, RetryPolicy
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend, QueueTask
from tools.sandbox_runner import SandboxResult
from workers.agent_worker import AgentWorker


class _FlakyTaskHandler:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, task: QueueTask) -> dict[str, str]:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("temporary failure")
        return {"task_id": task.task_id, "ok": "yes"}


def test_retry_engine_retries_transient_failures() -> None:
    sleeps: list[float] = []
    attempts = {"count": 0}
    retry_engine = RetryEngine(
        policies={"default": RetryPolicy(max_retries=2, base_delay_seconds=0.01, jitter_ratio=0.0)},
        sleep_fn=lambda duration: sleeps.append(duration),
    )

    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TimeoutError("network blip")
        return "ok"

    assert retry_engine.execute("default", flaky) == "ok"
    assert attempts["count"] == 3
    assert sleeps == [0.01, 0.02]


def test_agent_worker_task_execution_uses_retry_engine() -> None:
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    task = QueueTask(task_id="retry-task", name="retry")
    queue.enqueue_task(task)

    handler = _FlakyTaskHandler()
    retry_engine = RetryEngine(
        policies={"task_execution": RetryPolicy(max_retries=2, base_delay_seconds=0.0, jitter_ratio=0.0)},
        sleep_fn=lambda _: None,
    )
    worker = AgentWorker(
        worker_id="worker-1",
        queue=queue,
        event_bus=EventBus(),
        task_handler=handler,
        retry_engine=retry_engine,
    )

    processed = worker.process_once()
    assert processed is True
    assert handler.calls == 2
    assert worker.telemetry.processed_tasks == 1


def test_queue_worker_permanent_failures_dead_letter_immediately() -> None:
    retry_engine = RetryEngine(
        policies={"queue_worker": RetryPolicy(max_retries=3, base_delay_seconds=0.0, jitter_ratio=0.0)}
    )
    queue = DistributedTaskQueue(InMemoryQueueBackend(), max_retries=3, retry_engine=retry_engine)
    task = QueueTask(task_id="bad-task", name="bad")
    queue.enqueue_task(task)
    inflight = queue.dequeue_task(timeout_seconds=0)
    assert inflight is not None

    queue.fail_task(inflight, error="validation failed", exc=ValueError("validation failed"))

    assert queue.dead_letter_size() == 1
    assert queue.queue_size() == 0


def test_execution_gateway_retries_external_api_tools(monkeypatch) -> None:
    calls = {"count": 0}

    def _mock_run_callable(handler, *args, **kwargs):
        calls["count"] += 1
        if calls["count"] < 3:
            return SandboxResult(ok=False, error="remote api timeout")
        return SandboxResult(ok=True, output={"ok": True})

    monkeypatch.setattr("core.execution_gateway.DEFAULT_SANDBOX_RUNNER.run_callable", _mock_run_callable)

    retry_engine = RetryEngine(
        policies={"external_api": RetryPolicy(max_retries=3, base_delay_seconds=0.0, jitter_ratio=0.0)},
        sleep_fn=lambda _: None,
    )
    gateway = ExecutionGateway(
        policy=GatewayPolicy(require_approval_categories=set(), blocked_tools=set()),
        retry_engine=retry_engine,
    )

    result = gateway.execute_tool(
        tool_name="api_execution",
        category="integration",
        handler=lambda: {"ok": True},
        args=(),
        kwargs={},
    )

    assert result == {"ok": True}
    assert calls["count"] == 3
