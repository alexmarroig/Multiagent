"""Centralized retry policy engine used across execution paths."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable

from monitoring.structured_logging import log_event
from monitoring.tracing import get_tracer


TRANSIENT = "transient"
PERMANENT = "permanent"


@dataclass(slots=True)
class RetryPolicy:
    max_retries: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    jitter_ratio: float = 0.2


class RetryEngine:
    """Executes callables using operation-specific retry policies."""

    def __init__(
        self,
        *,
        policies: dict[str, RetryPolicy] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        random_fn: Callable[[float, float], float] = random.uniform,
        logger: logging.Logger | None = None,
    ) -> None:
        self._policies = policies or {}
        self._sleep_fn = sleep_fn
        self._random_fn = random_fn
        self._logger = logger or logging.getLogger(__name__)
        self._tracer = get_tracer()

    def get_policy(self, operation: str) -> RetryPolicy:
        return self._policies.get(operation, self._policies.get("default", RetryPolicy()))

    def classify_failure(self, operation: str, failure: BaseException | str, *, context: dict[str, Any] | None = None) -> str:
        if isinstance(failure, str):
            normalized = failure.lower()
            permanent_markers = ("validation", "permission", "auth", "not found", "unsupported", "invalid")
            transient_markers = ("timeout", "tempor", "throttle", "rate limit", "unavailable", "busy")
            if any(marker in normalized for marker in permanent_markers):
                return PERMANENT
            if any(marker in normalized for marker in transient_markers):
                return TRANSIENT
            return TRANSIENT

        if isinstance(failure, (ValueError, TypeError, KeyError, PermissionError, FileNotFoundError)):
            return PERMANENT
        if isinstance(failure, (TimeoutError, ConnectionError)):
            return TRANSIENT
        # Most runtime integration failures are recoverable by default.
        return TRANSIENT

    def compute_delay(self, operation: str, attempt_number: int) -> float:
        policy = self.get_policy(operation)
        capped_attempt = max(1, attempt_number)
        backoff = min(
            policy.max_delay_seconds,
            policy.base_delay_seconds * (policy.backoff_multiplier ** (capped_attempt - 1)),
        )
        jitter_window = backoff * max(0.0, policy.jitter_ratio)
        jitter = self._random_fn(-jitter_window, jitter_window) if jitter_window > 0 else 0.0
        return max(0.0, backoff + jitter)

    def execute(
        self,
        operation: str,
        func: Callable[..., Any],
        *args: Any,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        policy = self.get_policy(operation)
        context_fields = dict(context or {})
        for attempt in range(1, policy.max_retries + 2):
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                classification = self.classify_failure(operation, exc, context=context_fields)
                trace_context = self._tracer.current_context()
                log_event(
                    self._logger,
                    component="retry_engine",
                    event="retry_attempt_failed",
                    severity="warning",
                    operation=operation,
                    attempt=attempt,
                    max_retries=policy.max_retries,
                    classification=classification,
                    error=str(exc),
                    trace_id=trace_context.trace_id if trace_context else None,
                    span_id=trace_context.span_id if trace_context else None,
                    **context_fields,
                )
                if classification == PERMANENT or attempt > policy.max_retries:
                    log_event(
                        self._logger,
                        component="retry_engine",
                        event="retry_exhausted",
                        severity="error",
                        operation=operation,
                        attempt=attempt,
                        classification=classification,
                        error=str(exc),
                        **context_fields,
                    )
                    raise
                delay = self.compute_delay(operation, attempt)
                log_event(
                    self._logger,
                    component="retry_engine",
                    event="retry_scheduled",
                    severity="info",
                    operation=operation,
                    attempt=attempt,
                    delay_seconds=round(delay, 3),
                    classification=classification,
                    **context_fields,
                )
                self._sleep_fn(delay)


def get_default_retry_engine() -> RetryEngine:
    return RetryEngine(
        policies={
            "default": RetryPolicy(max_retries=2, base_delay_seconds=0.1, max_delay_seconds=1.0, jitter_ratio=0.15),
            "task_execution": RetryPolicy(max_retries=3, base_delay_seconds=0.2, max_delay_seconds=2.0, jitter_ratio=0.2),
            "tool_call": RetryPolicy(max_retries=2, base_delay_seconds=0.1, max_delay_seconds=1.0, jitter_ratio=0.2),
            "external_api": RetryPolicy(max_retries=4, base_delay_seconds=0.3, max_delay_seconds=5.0, jitter_ratio=0.25),
            "queue_worker": RetryPolicy(max_retries=3, base_delay_seconds=0.5, max_delay_seconds=8.0, jitter_ratio=0.3),
        }
    )
