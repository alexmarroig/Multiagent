"""Global LLM/model gateway: quota, policy, routing, and audit logging."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Callable

from core.quota_ledger import DurableQuotaLedger, QuotaDebit
from governance.audit_ledger import AuditLedger
from monitoring.structured_logging import log_event
from monitoring.tracing import get_tracer
from security.tenant_context import TenantContext, require_tenant_context


@dataclass(slots=True)
class ModelRequest:
    prompt: str
    model: str
    max_tokens: int
    estimated_tokens: int
    estimated_cost: float
    metadata: dict[str, Any]


class ModelGateway:
    def __init__(
        self,
        *,
        quota_ledger: DurableQuotaLedger,
        model_router: dict[str, Callable[[ModelRequest], str]] | None = None,
        audit_ledger: AuditLedger | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.quota_ledger = quota_ledger
        self.model_router = model_router or {}
        self.audit_ledger = audit_ledger
        self.logger = logger or logging.getLogger(__name__)
        self.tracer = get_tracer()

    def register_model(self, model: str, handler: Callable[[ModelRequest], str]) -> None:
        self.model_router[model] = handler

    def _validate_policy(self, request: ModelRequest) -> None:
        if request.max_tokens <= 0 or request.estimated_tokens <= 0:
            raise ValueError("token bounds must be positive")
        if request.estimated_tokens > request.max_tokens * 2:
            raise ValueError("estimated tokens exceed policy envelope")

    def _fallback_handler(self, request: ModelRequest) -> str:
        text = request.prompt.strip().replace("\n", " ")
        return text[: min(240, request.max_tokens)]

    def call(self, request: ModelRequest, *, context: TenantContext) -> dict[str, Any]:
        enforced = require_tenant_context(context)
        self._validate_policy(request)

        with self.tracer.start_span(
            "model_gateway.call",
            kind="llm_call",
            attributes={
                "tenant_id": enforced.tenant_id,
                "agent_id": enforced.agent_id,
                "request_id": enforced.request_id,
                "trace_id": enforced.trace_id,
                "model": request.model,
            },
        ) as span:
            usage = self.quota_ledger.debit(
                QuotaDebit(
                    tenant_id=enforced.tenant_id,
                    agent_id=enforced.agent_id,
                    request_id=enforced.request_id,
                    tokens=request.estimated_tokens,
                    cost=request.estimated_cost,
                )
            )
            handler = self.model_router.get(request.model, self._fallback_handler)
            output = handler(request)
            log_event(
                self.logger,
                component="model_gateway",
                event="llm_call_executed",
                tenant_id=enforced.tenant_id,
                agent_id=enforced.agent_id,
                request_id=enforced.request_id,
                trace_id=span.trace_id,
                model=request.model,
                usage=usage,
            )
            if self.audit_ledger is not None:
                self.audit_ledger.record_tool_execution(
                    actor=enforced.agent_id,
                    tool=f"model:{request.model}",
                    status="success",
                    metadata={"tenant_id": enforced.tenant_id, "request_id": enforced.request_id, "prompt_hash": hashlib.sha256(request.prompt.encode()).hexdigest()},
                )
            return {"output": output, "usage": usage, "model": request.model}
