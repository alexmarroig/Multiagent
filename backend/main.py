"""Aplicação principal FastAPI do módulo backend AgentOS."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery

from api.routes_agents import router as agents_router
from api.routes_tools import router as tools_router
from api.websocket import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentos-backend")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("AgentOS backend iniciando...")
    yield
    logger.info("AgentOS backend finalizado.")


app = FastAPI(title="AgentOS Backend", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)
app.include_router(tools_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


celery_app = Celery("agentos", broker="redis://redis:6379/0", backend="redis://redis:6379/0")
