"""Aplicação principal FastAPI do módulo backend AgentOS."""

from __future__ import annotations

import logging
import os
import signal
import sys
from pathlib import Path

from celery import Celery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from api.routes_agents import router as agents_router
from api.routes_auth import router as auth_router
from api.routes_flows import router as flows_router
from api.routes_governance import router as governance_router
from api.routes_history import router as history_router
from api.routes_metrics import router as metrics_router
from api.routes_tools import router as tools_router
from api.websocket import router as ws_router

from config import current_pid, settings
from observability.logging import log_structured
from monitoring.system_health import router as system_health_router

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s service=agentos-backend env=%(app_env)s message=%(message)s",
)

base_logger = logging.getLogger("agentos-backend")
logger = logging.LoggerAdapter(base_logger, {"app_env": settings.app_env})


# ------------------------------------------------------------------
# Runtime utilities
# ------------------------------------------------------------------

def get_runtime_port() -> int:
    """Lê e valida a porta de execução a partir da variável de ambiente PORT."""
    raw_port = os.getenv("PORT")

    if not raw_port:
        raise RuntimeError("PORT environment variable is required")

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise RuntimeError("PORT must be an integer") from exc

    if not (1 <= port <= 65535):
        raise RuntimeError("PORT must be between 1 and 65535")

    return port


# ------------------------------------------------------------------
# Lifespan
# ------------------------------------------------------------------

async def lifespan(_: FastAPI):

    settings.validate_runtime()

    runtime_port = get_runtime_port()

    log_structured(
        logger,
        "startup",
        agent_id="system",
        pid=current_pid(),
        port=runtime_port,
    )

    def _handle_signal(signum, _frame):
        log_structured(
            logger,
            "shutdown_signal_received",
            agent_id="system",
            signal=signum,
        )

    try:
        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
    except ValueError:
        # Happens in some multi-worker environments
        pass

    yield

    log_structured(
        logger,
        "shutdown_complete",
        agent_id="system",
        pid=current_pid(),
    )


# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------

app = FastAPI(
    title="AgentOS Backend",
    version="0.4.1",
    lifespan=lifespan,
)

allowed_origins = [
    "http://localhost:3000",
    "http://frontend:3000",
    settings.frontend_url,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agents_router)
app.include_router(flows_router, prefix="/api/flows", tags=["Flows"])
app.include_router(history_router, prefix="/api/history", tags=["History"])
app.include_router(metrics_router)
app.include_router(tools_router)
app.include_router(governance_router)
app.include_router(ws_router)
app.include_router(system_health_router)


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ------------------------------------------------------------------
# Celery
# ------------------------------------------------------------------

celery_app = Celery(
    "agentos",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


# ------------------------------------------------------------------
# Local dev entrypoint
# ------------------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    port = get_runtime_port()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
