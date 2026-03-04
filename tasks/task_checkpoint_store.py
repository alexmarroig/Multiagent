"""Durable checkpoint store for task graph execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TaskCheckpointStore:
    def __init__(self, path: str | Path = ".agentos/checkpoints.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, checkpoint: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(checkpoint, sort_keys=True) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
