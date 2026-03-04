"""Circuit breaker controls for external tools and critical integrations."""

from __future__ import annotations

import json
import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from time import monotonic
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitBreakerConfig:
    failure_rate_threshold: float = 0.5
    min_calls: int = 6
    sample_window: int = 20
    cooldown_seconds: float = 30.0
    half_open_max_calls: int = 3


@dataclass(slots=True)
class CircuitStats:
    state: CircuitState = CircuitState.CLOSED
    opened_at: float | None = None
    recent_results: deque[bool] = field(default_factory=lambda: deque(maxlen=20))
    half_open_attempts: int = 0
    half_open_successes: int = 0

    def failure_rate(self) -> float:
        if not self.recent_results:
            return 0.0
        failures = sum(1 for ok in self.recent_results if not ok)
        return failures / len(self.recent_results)


class CircuitOpenError(RuntimeError):
    """Raised when a call is blocked because the circuit is open."""


class CircuitBreakerManager:
    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._lock = Lock()
        self._circuits: dict[str, CircuitStats] = {}

    def _stats_for(self, key: str) -> CircuitStats:
        stats = self._circuits.get(key)
        if stats is None:
            stats = CircuitStats(recent_results=deque(maxlen=self._config.sample_window))
            self._circuits[key] = stats
        return stats

    def _emit_alert(self, key: str, stats: CircuitStats, reason: str) -> None:
        logger.warning(
            "Circuit breaker opened for '%s' (failure_rate=%.2f, sample_size=%s, reason=%s)",
            key,
            stats.failure_rate(),
            len(stats.recent_results),
            reason,
        )

    def _maybe_allow_half_open(self, stats: CircuitStats) -> None:
        if stats.state != CircuitState.OPEN:
            return
        if stats.opened_at is None:
            return
        if monotonic() - stats.opened_at < self._config.cooldown_seconds:
            return
        stats.state = CircuitState.HALF_OPEN
        stats.half_open_attempts = 0
        stats.half_open_successes = 0

    def before_call(self, key: str) -> None:
        with self._lock:
            stats = self._stats_for(key)
            self._maybe_allow_half_open(stats)

            if stats.state == CircuitState.OPEN:
                raise CircuitOpenError(f"Circuit breaker open for '{key}'")

            if stats.state == CircuitState.HALF_OPEN and stats.half_open_attempts >= self._config.half_open_max_calls:
                raise CircuitOpenError(f"Circuit breaker half-open retry budget exhausted for '{key}'")

            if stats.state == CircuitState.HALF_OPEN:
                stats.half_open_attempts += 1

    def after_call(self, key: str, success: bool) -> None:
        with self._lock:
            stats = self._stats_for(key)
            stats.recent_results.append(success)

            if stats.state == CircuitState.HALF_OPEN:
                if not success:
                    stats.state = CircuitState.OPEN
                    stats.opened_at = monotonic()
                    self._emit_alert(key, stats, "half_open_failure")
                    return

                stats.half_open_successes += 1
                if stats.half_open_successes >= self._config.half_open_max_calls:
                    stats.state = CircuitState.CLOSED
                    stats.opened_at = None
                    stats.half_open_attempts = 0
                    stats.half_open_successes = 0
                return

            if stats.state == CircuitState.CLOSED and len(stats.recent_results) >= self._config.min_calls:
                if stats.failure_rate() >= self._config.failure_rate_threshold:
                    stats.state = CircuitState.OPEN
                    stats.opened_at = monotonic()
                    self._emit_alert(key, stats, "failure_rate_threshold")

    def invoke(self, key: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        self.before_call(key)
        success = False
        try:
            result = fn(*args, **kwargs)
            success = _tool_result_success(result)
            return result
        except Exception:
            success = False
            raise
        finally:
            self.after_call(key, success)

    def snapshot(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                key: {
                    "state": stats.state.value,
                    "failure_rate": round(stats.failure_rate(), 4),
                    "sample_size": len(stats.recent_results),
                    "half_open_attempts": stats.half_open_attempts,
                }
                for key, stats in self._circuits.items()
            }


def _tool_result_success(result: Any) -> bool:
    if isinstance(result, dict):
        if result.get("success") is False:
            return False
        return not bool(result.get("error"))

    if isinstance(result, str):
        lowered = result.lower()
        if "error" in lowered or "erro" in lowered or "falha" in lowered:
            return False
        try:
            parsed = json.loads(result)
        except Exception:
            return True
        if isinstance(parsed, dict):
            if parsed.get("success") is False:
                return False
            return not bool(parsed.get("error"))
        return True

    return True


circuit_breakers = CircuitBreakerManager()
