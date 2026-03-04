"""Durable knowledge base with namespace scoping."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class KnowledgeStore:
    def __init__(self) -> None:
        self._namespaces: dict[str, dict[str, Any]] = defaultdict(dict)

    def upsert(self, namespace: str, key: str, value: Any) -> None:
        self._namespaces[namespace][key] = value

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        return self._namespaces.get(namespace, {}).get(key, default)

    def list_namespace(self, namespace: str) -> dict[str, Any]:
        return dict(self._namespaces.get(namespace, {}))
