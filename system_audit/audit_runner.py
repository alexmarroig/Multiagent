from __future__ import annotations

import json
import sys

from system_audit.checkpoint_audit import run_audit as run_checkpoint_audit
from system_audit.circuit_breaker_audit import run_audit as run_circuit_breaker_audit
from system_audit.context_management_audit import run_audit as run_context_management_audit
from system_audit.llm_budget_audit import run_audit as run_llm_budget_audit
from system_audit.queue_backpressure_audit import run_audit as run_queue_backpressure_audit
from system_audit.task_explosion_audit import run_audit as run_task_explosion_audit
from system_audit.worker_watchdog_audit import run_audit as run_worker_watchdog_audit


AUDITS = [
    run_task_explosion_audit,
    run_queue_backpressure_audit,
    run_llm_budget_audit,
    run_context_management_audit,
    run_circuit_breaker_audit,
    run_worker_watchdog_audit,
    run_checkpoint_audit,
]


def main() -> int:
    reports = [runner() for runner in AUDITS]
    overall_status = "OK"
    if any(report["status"] == "FAILED" for report in reports):
        overall_status = "FAILED"
    elif any(report["status"] == "PARTIAL" for report in reports):
        overall_status = "PARTIAL"

    output = {"overall_status": overall_status, "audits": reports}
    print(json.dumps(output, indent=2))

    if any(report["status"] == "FAILED" for report in reports):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
