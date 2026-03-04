from __future__ import annotations

from backend.tools.circuit_breaker import CircuitBreakerConfig, CircuitBreakerManager, CircuitOpenError


def run_audit() -> dict[str, object]:
    name = "Circuit Breaker"
    try:
        manager = CircuitBreakerManager(CircuitBreakerConfig(min_calls=3, failure_rate_threshold=0.6, sample_window=5))
        key = "tool.search"
        for _ in range(3):
            manager.after_call(key, success=False)
        status = "PARTIAL"
        try:
            manager.before_call(key)
        except CircuitOpenError:
            status = "OK"
        return {"name": name, "status": status, "details": {"snapshot": manager.snapshot().get(key)}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
