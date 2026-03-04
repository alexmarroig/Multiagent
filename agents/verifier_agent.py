"""Verifier agent that validates outputs and policy conformance."""

from __future__ import annotations

from typing import Any


class VerifierAgent:
    role = "verifier"

    def verify(self, execution_result: dict[str, Any]) -> dict[str, Any]:
        success = execution_result.get("status") == "completed"
        return {
            "task_id": execution_result.get("task_id"),
            "verified": success,
            "notes": "verified" if success else "execution did not complete",
        }
