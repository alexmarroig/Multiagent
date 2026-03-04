from core.task_queue import DistributedTaskQueue, InMemoryQueueBackend
from tasks.task_graph_engine import TaskGraphEngine


def _task_payload(task_id: str) -> dict:
    return {"task_id": task_id, "name": f"task-{task_id}"}


def test_queue_watermarks_pause_and_resume_scheduling():
    queue = DistributedTaskQueue(
        InMemoryQueueBackend(),
        queue_high_watermark=2,
        queue_low_watermark=1,
    )

    queue.enqueue_task(_task_payload("1"))
    queue.enqueue_task(_task_payload("2"))
    assert queue.can_schedule_new_tasks()

    queue.enqueue_task(_task_payload("3"))
    assert not queue.can_schedule_new_tasks()

    queue.dequeue_task()
    assert not queue.can_schedule_new_tasks()

    queue.dequeue_task()
    queue.dequeue_task()
    assert queue.can_schedule_new_tasks()


def test_task_scheduler_obeys_queue_pressure_before_spawning():
    queue = DistributedTaskQueue(
        InMemoryQueueBackend(),
        queue_high_watermark=2,
        queue_low_watermark=1,
    )

    queue.enqueue_task(_task_payload("already-pending-1"))
    queue.enqueue_task(_task_payload("already-pending-2"))
    queue.enqueue_task(_task_payload("already-pending-3"))
    engine = TaskGraphEngine(queue)
    engine.add_task(task_id="next", name="next")

    scheduled = engine.schedule_ready_tasks()
    assert scheduled == []
    assert engine._tasks["next"].status == "pending"

    queue.dequeue_task()
    scheduled = engine.schedule_ready_tasks()
    assert scheduled == []

    queue.dequeue_task()
    queue.dequeue_task()
    scheduled = engine.schedule_ready_tasks()
    assert len(scheduled) == 1
    assert scheduled[0].task_id == "next"
