"""Agent communication bus supporting direct messages, broadcasts, and delegation."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Message:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)


class MessageBus:
    def __init__(self) -> None:
        self._mailboxes: dict[str, deque[Message]] = defaultdict(deque)
        self._events: deque[Message] = deque()

    def send_message(self, to_agent: str, message: Message) -> None:
        self._mailboxes[to_agent].append(message)

    def broadcast(self, message: Message) -> None:
        self._events.append(message)
        for agent_id in self._mailboxes:
            self._mailboxes[agent_id].append(message)

    def delegate_task(self, *, from_agent: str, to_agent: str, task_id: str, payload: dict[str, Any]) -> None:
        self.send_message(
            to_agent,
            Message(
                topic="task.delegated",
                payload={"from": from_agent, "task_id": task_id, "payload": payload},
            ),
        )

    def receive(self, agent_id: str) -> Message | None:
        mailbox = self._mailboxes[agent_id]
        if not mailbox:
            return None
        return mailbox.popleft()

    def depth(self) -> int:
        return len(self._events) + sum(len(mailbox) for mailbox in self._mailboxes.values())
