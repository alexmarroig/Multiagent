"""Persistent vector memory for autonomous agents."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb


class VectorMemory:
    def __init__(self, session_id: str, persist_dir: str = "./outputs/vector_memory") -> None:
        self.session_id = session_id
        root = Path(persist_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(root))
        self.collection = self.client.get_or_create_collection(name=f"agent-memory-{session_id}")

    def _store(self, kind: str, payload: dict[str, Any]) -> str:
        doc_id = str(uuid.uuid4())
        content = json.dumps(payload, ensure_ascii=False)
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"kind": kind, "timestamp": datetime.utcnow().isoformat()}],
        )
        return doc_id

    def store_event(self, event: dict[str, Any]) -> str:
        return self._store("event", event)

    def store_task_result(self, task_id: str, result: Any) -> str:
        return self._store("task_result", {"task_id": task_id, "result": result})

    def retrieve_context(self, limit: int = 10) -> list[dict[str, Any]]:
        records = self.collection.get(limit=limit, include=["metadatas", "documents"])
        documents = records.get("documents", []) or []
        metadata = records.get("metadatas", []) or []
        context: list[dict[str, Any]] = []
        for index, item in enumerate(documents):
            try:
                payload = json.loads(item)
            except json.JSONDecodeError:
                payload = {"raw": item}
            context.append({"metadata": metadata[index] if index < len(metadata) else {}, "payload": payload})
        return context

    def semantic_search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        result = self.collection.query(query_texts=[query], n_results=limit)
        docs = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        return [{"metadata": metadatas[i] if i < len(metadatas) else {}, "document": doc} for i, doc in enumerate(docs)]
