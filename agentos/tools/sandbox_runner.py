"""Sandbox runner for isolated tool execution with resource and access controls."""

from __future__ import annotations

import builtins
import io
import multiprocessing
import os
import resource
import socket
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass(slots=True)
class SandboxPolicy:
    """Execution policy for sandboxed tool invocations."""

    timeout_seconds: int = 30
    cpu_seconds: int = 10
    memory_limit_mb: int = 512
    network_enabled: bool = False
    writable_paths: tuple[Path, ...] = field(default_factory=tuple)
    readable_paths: tuple[Path, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class SandboxResult:
    """Result envelope returned by sandboxed execution."""

    ok: bool
    output: Any = None
    error: str = ""


class SandboxRunner:
    """Executes callables in a subprocess with strict limits."""

    def __init__(self, *, default_policy: SandboxPolicy | None = None) -> None:
        self.default_policy = default_policy or SandboxPolicy()

    def run_callable(
        self,
        func: Callable[..., Any],
        *args: Any,
        policy: SandboxPolicy | None = None,
        **kwargs: Any,
    ) -> SandboxResult:
        effective = policy or self.default_policy
        with tempfile.TemporaryDirectory(prefix="tool-sandbox-") as temp_dir:
            queue: multiprocessing.Queue[SandboxResult] = multiprocessing.Queue(maxsize=1)
            process = _mp_context().Process(
                target=_sandbox_entry,
                args=(queue, func, args, kwargs, effective, temp_dir),
                daemon=True,
            )
            process.start()
            process.join(timeout=effective.timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join()
                return SandboxResult(ok=False, error="sandbox timeout exceeded")
            if queue.empty():
                return SandboxResult(ok=False, error="sandbox terminated without result")
            return queue.get()


def _mp_context() -> multiprocessing.context.BaseContext:
    try:
        return multiprocessing.get_context("fork")
    except ValueError:
        return multiprocessing.get_context()


def _sandbox_entry(
    queue: multiprocessing.Queue[SandboxResult],
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    policy: SandboxPolicy,
    temp_dir: str,
) -> None:
    try:
        _apply_limits(policy)
        os.chdir(temp_dir)
        _apply_filesystem_restrictions(policy, Path(temp_dir))
        _apply_network_restrictions(policy)
        output = func(*args, **kwargs)
        queue.put(SandboxResult(ok=True, output=output))
    except Exception as exc:  # pragma: no cover - defensive sandbox boundary
        queue.put(SandboxResult(ok=False, error=str(exc)))


def _apply_limits(policy: SandboxPolicy) -> None:
    memory_bytes = policy.memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (policy.cpu_seconds, policy.cpu_seconds + 1))


def _apply_network_restrictions(policy: SandboxPolicy) -> None:
    if policy.network_enabled:
        return

    class _BlockedSocket(socket.socket):
        def __init__(self, *_: Any, **__: Any) -> None:
            raise PermissionError("network access disabled in sandbox")

    socket.socket = _BlockedSocket

    def _blocked_connection(*_: Any, **__: Any) -> Any:
        raise PermissionError("network access disabled in sandbox")

    socket.create_connection = _blocked_connection


def _apply_filesystem_restrictions(policy: SandboxPolicy, sandbox_dir: Path) -> None:
    readable = {_resolve_bound_path(path, sandbox_dir) for path in policy.readable_paths}
    writable = {_resolve_bound_path(path, sandbox_dir) for path in policy.writable_paths}

    readable.add(sandbox_dir)
    writable.add(sandbox_dir)

    original_open = builtins.open

    def _sandbox_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        candidate = _resolve_user_path(file, sandbox_dir)
        _ensure_path_allowed(candidate, writable if any(flag in mode for flag in ("w", "a", "+", "x")) else readable)
        return original_open(file, mode, *args, **kwargs)

    builtins.open = _sandbox_open
    io.open = _sandbox_open



def _resolve_bound_path(path: Path, sandbox_dir: Path) -> Path:
    return path if path.is_absolute() else (sandbox_dir / path).resolve()


def _resolve_user_path(file: Any, sandbox_dir: Path) -> Path:
    candidate = Path(file) if not isinstance(file, Path) else file
    return candidate if candidate.is_absolute() else (sandbox_dir / candidate).resolve()


def _ensure_path_allowed(candidate: Path, allowed_roots: set[Path]) -> None:
    resolved = candidate.resolve()
    if any(_is_relative_to(resolved, root) for root in allowed_roots):
        return
    raise PermissionError(f"filesystem access denied: {candidate}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


DEFAULT_SANDBOX_RUNNER = SandboxRunner()
