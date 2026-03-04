"""Persistent vector memory for autonomous agents."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb

from agentos.backend.security.rbac import (
    Permission,
    RBACAuthorizationError,
    RBACContext,
    RBACResource,
    SYSTEM_CONTEXT,
    rbac_middleware,
)


class VectorMemory:
    def __init__(self, session_id: str, persist_dir: str = "./outputs/vector_memory", tenant_id: str | None = None) -> None:
        self.session_id = session_id
        self.tenant_id = tenant_id
        root = Path(persist_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(root))
        self.collection = self.client.get_or_create_collection(name=f"agent-memory-{session_id}")

    def _resolve_context(self, actor: dict[str, Any] | RBACContext | None) -> RBACContext:
        if actor is None:
            return SYSTEM_CONTEXT
        if isinstance(actor, RBACContext):
            return actor
        return rbac_middleware.context_from_user(actor, fallback_roles=("operator",))

    def _authorize(self, permission: Permission, actor: dict[str, Any] | RBACContext | None) -> None:
        context = self._resolve_context(actor)
        try:
            rbac_middleware.authorize(
                context=context,
                permission=permission,
                resource=RBACResource(
                    resource_type="memory",
                    action=str(permission),
                    resource_id=self.session_id,
                    tenant_id=self.tenant_id,
                    scope="tenant" if self.tenant_id else "global",
                ),
            )
        except RBACAuthorizationError as exc:
            raise PermissionError(str(exc)) from exc

    def _store(self, kind: str, payload: dict[str, Any], *, actor: dict[str, Any] | RBACContext | None = None) -> str:
        self._authorize(Permission.MEMORY_WRITE, actor)
        doc_id = str(uuid.uuid4())
        content = json.dumps(payload, ensure_ascii=False)
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[{"kind": kind, "timestamp": datetime.utcnow().isoformat()}],
        )
        return doc_id

    def store_event(self, event: dict[str, Any], *, actor: dict[str, Any] | RBACContext | None = None) -> str:
        return self._store("event", event, actor=actor)

    def store_task_result(self, task_id: str, result: Any, *, actor: dict[str, Any] | RBACContext | None = None) -> str:
        return self._store("task_result", {"task_id": task_id, "result": result}, actor=actor)

    def retrieve_context(self, limit: int = 10, *, actor: dict[str, Any] | RBACContext | None = None) -> list[dict[str, Any]]:
        self._authorize(Permission.MEMORY_READ, actor)
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

    def semantic_search(
        self,
        query: str,
        limit: int = 5,
        *,
        actor: dict[str, Any] | RBACContext | None = None,
    ) -> list[dict[str, Any]]:
        self._authorize(Permission.MEMORY_READ, actor)
        result = self.collection.query(query_texts=[query], n_results=limit)
        docs = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        return [{"metadata": metadatas[i] if i < len(metadatas) else {}, "document": doc} for i, doc in enumerate(docs)]
