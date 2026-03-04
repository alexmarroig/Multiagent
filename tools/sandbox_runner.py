"""Sandbox runner abstraction for safe tool execution."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str


class SandboxRunner:
    def run(self, command: list[str], timeout_seconds: int = 30) -> SandboxResult:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return SandboxResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
