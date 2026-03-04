"""Per-agent mailbox for reliable command and event delivery."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class MailMessage:
    sender: str
    recipient: str
    subject: str
    body: dict[str, Any]
    timestamp: str


class AgentMailbox:
    def __init__(self) -> None:
        self._boxes: dict[str, list[MailMessage]] = defaultdict(list)

    def send(self, sender: str, recipient: str, subject: str, body: dict[str, Any]) -> None:
        self._boxes[recipient].append(
            MailMessage(
                sender=sender,
                recipient=recipient,
                subject=subject,
                body=body,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

    def receive(self, recipient: str, limit: int = 20) -> list[MailMessage]:
        messages = self._boxes[recipient][: max(limit, 1)]
        self._boxes[recipient] = self._boxes[recipient][len(messages) :]
        return messages
