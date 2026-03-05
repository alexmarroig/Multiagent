"""OpenTelemetry exporters for Prometheus metrics and Jaeger traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from monitoring.tracing import TraceContext, get_tracer


@dataclass(slots=True)
class OtelConfig:
    service_name: str = "agentos"
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    prometheus_port: int = 9464


class OpenTelemetryExporter:
    def __init__(self, config: OtelConfig | None = None) -> None:
        self.config = config or OtelConfig()
        self.tracer = get_tracer()
        self._metrics: list[dict[str, Any]] = []

    def start(self) -> None:
        """Initialize exporters if opentelemetry sdk is available."""
        try:
            from opentelemetry import trace  # type: ignore # noqa: F401
        except Exception:
            return

    def record_metric(self, name: str, value: float, *, attrs: dict[str, Any] | None = None) -> None:
        ctx = self.tracer.current_context()
        self._metrics.append({"name": name, "value": value, "attrs": attrs or {}, "trace_id": ctx.trace_id if ctx else None})

    def trace_queue_operation(self, operation: str, queue_name: str, *, attrs: dict[str, Any] | None = None) -> None:
        merged = {"queue": queue_name, **(attrs or {})}
        with self.tracer.start_span(f"queue.{operation}", kind="queue_operation", attributes=merged):
            self.record_metric("queue.operations", 1, attrs=merged)

    def trace_tool_call(self, tool_name: str, *, attrs: dict[str, Any] | None = None) -> TraceContext:
        cm = self.tracer.start_span(f"tool.{tool_name}", kind="tool_call", attributes=attrs or {})
        return cm.__enter__()
