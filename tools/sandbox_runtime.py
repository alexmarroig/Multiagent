"""Sandboxed tool execution runtime for isolated and safer tool invocations."""

from __future__ import annotations

import resource
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str


class SandboxRuntime:
    """Runs tool commands in temporary isolated process environments with resource controls."""

    def __init__(self, *, timeout_seconds: int = 30, memory_limit_mb: int = 512, cpu_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_seconds = cpu_seconds

    def _apply_limits(self) -> None:
        resource.setrlimit(resource.RLIMIT_AS, (self.memory_limit_mb * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds + 1))

    def run_tool(self, command: list[str], *, input_text: str | None = None) -> SandboxResult:
        with tempfile.TemporaryDirectory(prefix="agentos-sandbox-") as tmp_dir:
            proc = subprocess.run(
                command,
                input=input_text,
                text=True,
                capture_output=True,
                cwd=Path(tmp_dir),
                timeout=self.timeout_seconds,
                preexec_fn=self._apply_limits,
                check=False,
            )
            return SandboxResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
