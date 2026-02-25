"""Endpoints de métricas operacionais e dashboard."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from observability.metrics import metrics_store

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
async def get_metrics() -> dict:
    """Retorna snapshot de métricas de execução, tools e websocket."""
    return metrics_store.snapshot()


@router.get("/dashboard", response_class=HTMLResponse)
async def metrics_dashboard() -> str:
    """Dashboard HTML simples para monitorar métricas em tempo real."""
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>AgentOS • Métricas</title>
  <style>
    body { font-family: Inter, Arial, sans-serif; margin: 20px; background: #111827; color: #f9fafb; }
    h1 { margin-bottom: 8px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
    .card { background: #1f2937; border-radius: 10px; padding: 14px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #0f172a; padding: 8px; border-radius: 8px; }
    .muted { color: #9ca3af; font-size: 12px; }
  </style>
</head>
<body>
  <h1>Observabilidade AgentOS</h1>
  <p class="muted">Atualização automática a cada 5s</p>
  <div class="grid">
    <section class="card"><h2>Runs</h2><pre id="runs">carregando...</pre></section>
    <section class="card"><h2>Latência por task</h2><pre id="tasks">carregando...</pre></section>
    <section class="card"><h2>Erro por tool</h2><pre id="tools">carregando...</pre></section>
    <section class="card"><h2>Integrações externas</h2><pre id="external">carregando...</pre></section>
    <section class="card"><h2>WebSocket</h2><pre id="ws">carregando...</pre></section>
  </div>
  <script>
    async function refresh() {
      const res = await fetch('/api/metrics');
      const data = await res.json();
      document.getElementById('runs').textContent = JSON.stringify(data.runs, null, 2);
      document.getElementById('tasks').textContent = JSON.stringify(data.tasks, null, 2);
      document.getElementById('tools').textContent = JSON.stringify(data.tools, null, 2);
      document.getElementById('external').textContent = JSON.stringify(data.external_integrations, null, 2);
      document.getElementById('ws').textContent = JSON.stringify(data.websocket, null, 2);
    }
    refresh();
    setInterval(refresh, 5000);
  </script>
</body>
</html>
"""
