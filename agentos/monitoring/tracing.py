"""OpenTelemetry-compatible tracing utilities for agent execution paths."""

from __future__ import annotations

import contextvars
import logging
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


_TRACE_CTX: contextvars.ContextVar["TraceContext | None"] = contextvars.ContextVar("trace_context", default=None)


@dataclass(slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


class Tracer:
    """Lightweight tracer with OpenTelemetry style IDs and parent/child span nesting."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def current_context(self) -> TraceContext | None:
        return _TRACE_CTX.get()

    @contextmanager
    def start_span(self, name: str, *, kind: str, attributes: dict[str, Any] | None = None) -> Iterator[TraceContext]:
        parent = self.current_context()
        ctx = TraceContext(
            trace_id=parent.trace_id if parent else secrets.token_hex(16),
            span_id=secrets.token_hex(8),
            parent_span=parent.span_id if parent else None,
            attributes=attributes or {},
        )
        token = _TRACE_CTX.set(ctx)
        start = time.perf_counter()
        self.logger.info(
            "trace.start",
            extra={"trace": {"name": name, "kind": kind, "trace_id": ctx.trace_id, "span_id": ctx.span_id, "parent_span": ctx.parent_span, **ctx.attributes}},
        )
        try:
            yield ctx
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 3)
            self.logger.info(
                "trace.end",
                extra={"trace": {"name": name, "kind": kind, "trace_id": ctx.trace_id, "span_id": ctx.span_id, "parent_span": ctx.parent_span, "duration_ms": elapsed_ms}},
            )
            _TRACE_CTX.reset(token)


GLOBAL_TRACER = Tracer()


def get_tracer() -> Tracer:
    return GLOBAL_TRACER
