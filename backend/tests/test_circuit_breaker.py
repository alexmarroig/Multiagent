from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.circuit_breaker import CircuitBreakerConfig, CircuitBreakerManager, CircuitOpenError


def test_opens_circuit_when_failure_rate_exceeds_threshold() -> None:
    manager = CircuitBreakerManager(
        CircuitBreakerConfig(
            failure_rate_threshold=0.5,
            min_calls=4,
            sample_window=4,
            cooldown_seconds=60,
            half_open_max_calls=2,
        )
    )

    for _ in range(2):
        manager.invoke("search", lambda: "ok")
    for _ in range(2):
        manager.invoke("search", lambda: "error: upstream timeout")

    snapshot = manager.snapshot()["search"]
    assert snapshot["state"] == "open"

    try:
        manager.invoke("search", lambda: "ok")
    except CircuitOpenError:
        pass
    else:
        raise AssertionError("Circuit should block calls while open")


def test_half_open_allows_limited_retries_after_cooldown() -> None:
    manager = CircuitBreakerManager(
        CircuitBreakerConfig(
            failure_rate_threshold=0.5,
            min_calls=2,
            sample_window=5,
            cooldown_seconds=0.01,
            half_open_max_calls=2,
        )
    )

    manager.invoke("finance", lambda: "error: provider down")
    manager.invoke("finance", lambda: "error: provider down")

    import time

    time.sleep(0.02)
    assert manager.invoke("finance", lambda: "ok") == "ok"
    assert manager.invoke("finance", lambda: "ok") == "ok"

    snapshot = manager.snapshot()["finance"]
    assert snapshot["state"] == "closed"
