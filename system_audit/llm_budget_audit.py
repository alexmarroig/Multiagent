from __future__ import annotations

from monitoring.alerts import AlertManager


def run_audit() -> dict[str, object]:
    name = "LLM Budget Enforcement"
    try:
        manager = AlertManager(llm_budget_limit=10.0)
        alerts = manager.evaluate_runtime_signals(queue_depth=0, error_rate=0.0, llm_cost=12.0)
        status = "OK" if any(a.category == "llm_budget_exceeded" for a in alerts) else "FAILED"
        return {"name": name, "status": status, "details": {"alerts_emitted": len(alerts)}}
    except Exception as exc:
        return {"name": name, "status": "FAILED", "details": {"error": str(exc)}}
