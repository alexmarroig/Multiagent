import json
import os

import pytest

from agentos.core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from tasks.task_graph_engine import TaskGraphEngine


def _build_engine(checkpoint_path, checkpoint_interval=1, auto_resume=True):
    queue = DistributedTaskQueue(InMemoryQueueBackend())
    return TaskGraphEngine(
        queue,
        checkpoint_path=checkpoint_path,
        checkpoint_interval=checkpoint_interval,
        auto_resume=auto_resume,
    )


def test_checkpoint_persists_graph_state_and_execution_pointer(tmp_path):
    checkpoint_path = tmp_path / "graph-checkpoint.json"
    engine = _build_engine(checkpoint_path)

    engine.add_task(task_id="task-a", name="task-a", priority=10)
    engine.add_task(task_id="task-b", name="task-b", dependencies=["task-a"], priority=20)
    scheduled = engine.schedule_ready_tasks()
    assert [task.task_id for task in scheduled] == ["task-a"]
    engine.mark_task_completed("task-a")

    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert payload["completed_tasks"] == ["task-a"]
    assert payload["pending_tasks"] == ["task-b"]
    assert payload["tasks"]["task-b"]["status"] == "pending"
    assert payload["execution_pointer"]["tasks_scheduled_total"] == 1
    assert payload["execution_pointer"]["last_scheduled_task_id"] == "task-a"


def test_resume_from_checkpoint_recovers_and_continues_execution(tmp_path):
    checkpoint_path = tmp_path / "graph-checkpoint.json"
    engine = _build_engine(checkpoint_path)

    engine.add_task(task_id="prepare", name="prepare")
    engine.add_task(task_id="execute", name="execute", dependencies=["prepare"])
    engine.schedule_ready_tasks(limit=1)
    engine.mark_task_completed("prepare")

    recovered_engine = _build_engine(checkpoint_path, auto_resume=True)
    scheduled = recovered_engine.schedule_ready_tasks(limit=1)

    assert [task.task_id for task in scheduled] == ["execute"]


def test_checkpoint_write_failure_does_not_corrupt_previous_checkpoint(tmp_path, monkeypatch):
    checkpoint_path = tmp_path / "graph-checkpoint.json"
    engine = _build_engine(checkpoint_path, checkpoint_interval=100)

    engine.add_task(task_id="stable", name="stable")
    engine.save_checkpoint()
    baseline = checkpoint_path.read_text(encoding="utf-8")

    def explode_replace(_src, _dst):
        raise OSError("simulated fs failure")

    monkeypatch.setattr(os, "replace", explode_replace)

    engine.add_task(task_id="new-task", name="new-task")
    with pytest.raises(OSError):
        engine.save_checkpoint()

    assert checkpoint_path.read_text(encoding="utf-8") == baseline
