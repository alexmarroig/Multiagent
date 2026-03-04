from __future__ import annotations

from pathlib import Path

from tools.sandbox_runner import SandboxPolicy, SandboxRunner


def _read_allowed_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _read_denied_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _network_probe() -> str:
    import socket

    socket.create_connection(("example.com", 80), timeout=1)
    return "connected"


def test_sandbox_blocks_network_access() -> None:
    runner = SandboxRunner(default_policy=SandboxPolicy(network_enabled=False))
    result = runner.run_callable(_network_probe)
    assert not result.ok
    assert "network access disabled" in result.error


def test_sandbox_restricts_filesystem_to_explicit_paths(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed.txt"
    allowed.write_text("ok", encoding="utf-8")

    denied = tmp_path / "denied.txt"
    denied.write_text("no", encoding="utf-8")

    runner = SandboxRunner()
    allowed_result = runner.run_callable(
        _read_allowed_file,
        str(allowed),
        policy=SandboxPolicy(readable_paths=(tmp_path,)),
    )
    denied_result = runner.run_callable(
        _read_denied_file,
        str(Path("/") / "etc" / "hosts"),
        policy=SandboxPolicy(readable_paths=(tmp_path,)),
    )

    assert allowed_result.ok
    assert allowed_result.output == "ok"
    assert not denied_result.ok
    assert "filesystem access denied" in denied_result.error
