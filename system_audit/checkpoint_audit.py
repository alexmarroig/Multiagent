from __future__ import annotations

from pathlib import Path

from communication.event_bus import EventBus
from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from tasks.task_graph_engine import TaskGraphEngine


def run_audit() -> dict[str, object]:
    name = "Checkpoint Recovery"
    checkpoint_path = Path(".tmp_task_graph_checkpoint.json")
    try:
        queue = DistributedTaskQueue(InMemoryQueueBackend())
        engine = TaskGraphEngine(queue=queue, checkpoint_path=checkpoint_path, auto_resume=False, event_bus=EventBus())
        engine.add_task(task_id="cp-1", name="checkpoint")
        engine.save_checkpoint()

        restored = TaskGraphEngine(queue=queue, checkpoint_path=checkpoint_path, auto_resume=False, event_bus=EventBus())
        loaded = restored.load_checkpoint()
        status = "OK" if loaded else "FAILED"
        return {"name": name, "status": status, "details": {"checkpoint_exists": checkpoint_path.exists()}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
    finally:
        if checkpoint_path.exists():
            checkpoint_path.unlink()
