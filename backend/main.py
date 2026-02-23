"""Aplicação principal FastAPI do módulo backend AgentOS."""

from __future__ import annotations

import logging
import signal

from celery import Celery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes_agents import router as agents_router
from api.routes_auth import router as auth_router
from api.routes_flows import router as flows_router
from api.routes_history import router as history_router
from api.routes_tools import router as tools_router
from api.websocket import router as ws_router
from config import current_pid, settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s service=agentos-backend env=%(app_env)s message=%(message)s",
)
logger = logging.LoggerAdapter(logging.getLogger("agentos-backend"), {"app_env": settings.app_env})


async def lifespan(_: FastAPI):
    settings.validate_runtime()
    logger.info("startup pid=%s port=%s", current_pid(), settings.port)

    def _handle_signal(signum, _frame):
        logger.info("shutdown_signal_received signal=%s", signum)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    yield

    logger.info("shutdown_complete pid=%s", current_pid())


app = FastAPI(title="AgentOS Backend", version="0.4.1", lifespan=lifespan)

allowed_origins = ["http://localhost:3000", "http://frontend:3000", settings.frontend_url]
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(set(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(agents_router)
app.include_router(flows_router, prefix="/api/flows", tags=["Flows"])
app.include_router(history_router, prefix="/api/history", tags=["History"])
app.include_router(tools_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict[str, str | int]:
    return {
        "status": "ok",
        "version": "0.4.1",
        "env": settings.app_env,
        "port": settings.port,
    }


celery_app = Celery("agentos", broker=settings.redis_url, backend=settings.redis_url)

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )
