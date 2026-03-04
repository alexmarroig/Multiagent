from core.context_manager import ContextWindowConfig, LLMContextManager
from memory.vector_memory import VectorMemory


def test_context_manager_retrieves_and_prioritizes_relevant_memory():
    memory = VectorMemory()
    memory.store_task_result("1", {"summary": "Fix payment retries for failed webhook delivery"})
    memory.store_environment_state({"queue_depth": 99, "region": "us-east-1"})
    memory.store_knowledge({"note": "Use idempotency keys when retrying payments"})

    manager = LLMContextManager(memory=memory, config=ContextWindowConfig(max_context_tokens=2048, reserved_response_tokens=512))
    context = manager.prepare_planner_context(goals=["improve webhook payment reliability"])

    assert context
    assert any(item.kind in {"task_result", "knowledge"} for item in context)


def test_context_manager_summarizes_and_truncates_for_small_windows():
    memory = VectorMemory()
    long_text = " ".join(["history"] * 2000)
    memory.store_knowledge({"transcript": long_text})
    memory.store_task_result("2", {"summary": "critical outage mitigation"})

    manager = LLMContextManager(memory=memory, config=ContextWindowConfig(max_context_tokens=512, reserved_response_tokens=256))
    context = manager.prepare_planner_context(goals=["stabilize production"])

    assert any(item.kind == "summary" for item in context)
    total_tokens = sum(manager._estimate_tokens(manager._record_text(item)) for item in context)
    assert total_tokens <= manager.config.prompt_budget_tokens


def test_context_manager_chunks_large_goal_input():
    memory = VectorMemory()
    huge_goal = " ".join(["launch"] * 900)

    manager = LLMContextManager(memory=memory, config=ContextWindowConfig(max_context_tokens=1024, reserved_response_tokens=300))
    context = manager.prepare_planner_context(goals=[huge_goal])

    chunk_count = sum(1 for item in context if item.kind in {"goal", "chunk"})
    assert chunk_count >= 2
