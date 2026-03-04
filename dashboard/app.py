from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from agentos.monitoring.system_health import health_service, router as health_router

app = FastAPI(title="Agent Platform Reliability Dashboard")
app.include_router(health_router)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    return """
<!doctype html>
<html>
  <head>
    <title>System Health Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; }
      .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
      .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
    </style>
  </head>
  <body>
    <h1>Autonomous Agent Platform Health</h1>
    <div class="grid" id="metrics"></div>
    <h2>Recent Alerts</h2>
    <pre id="alerts">No alerts</pre>
    <script>
      async function refresh() {
        const res = await fetch('/system/health');
        const data = await res.json();
        const metrics = document.getElementById('metrics');
        metrics.innerHTML = Object.entries(data).map(([k, v]) => `<div class="card"><strong>${k}</strong><div>${v}</div></div>`).join('');
      }
      refresh();
      setInterval(refresh, 5000);
    </script>
  </body>
</html>
"""


@app.post("/dashboard/mock-update")
async def mock_update() -> dict[str, float]:
    health_service.update_metrics(
        agents_active=120,
        queue_depth=450,
        worker_utilization=0.72,
        task_success_rate=0.97,
        error_rate=0.03,
        llm_token_consumption=120000,
        memory_usage=0.64,
    )
    return {"status": 1.0}
