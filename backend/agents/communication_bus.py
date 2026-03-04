"""In-process communication bus for agent collaboration."""

from __future__ import annotations

from collections import defaultdict
from queue import Empty, Queue
from typing import Any


class CommunicationBus:
    def __init__(self) -> None:
        self._mailboxes: dict[str, Queue[dict[str, Any]]] = defaultdict(Queue)

    def send_message(self, agent_id: str, payload: dict[str, Any]) -> None:
        self._mailboxes[agent_id].put(payload)

    def broadcast_event(self, event: dict[str, Any]) -> None:
        for mailbox in self._mailboxes.values():
            mailbox.put(event)

    def receive(self, agent_id: str, timeout: float = 0.01) -> dict[str, Any] | None:
        try:
            return self._mailboxes[agent_id].get(timeout=timeout)
        except Empty:
            return None
