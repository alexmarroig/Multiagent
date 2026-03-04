from __future__ import annotations

from agentos.core.context_manager import ContextWindowConfig, LLMContextManager
from memory.vector_memory import VectorMemory


def run_audit() -> dict[str, object]:
    name = "Context Management"
    try:
        memory = VectorMemory()
        manager = LLMContextManager(memory=memory, config=ContextWindowConfig(max_context_tokens=1024, reserved_response_tokens=256))
        records = manager.assemble_context(user_input=["A" * 2400])
        total_payload_chars = sum(len(str(item.payload)) for item in records)
        status = "OK" if total_payload_chars > 0 and len(records) > 0 else "PARTIAL"
        return {"name": name, "status": status, "details": {"records_selected": len(records)}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
