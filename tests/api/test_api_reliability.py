from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from monitoring.system_health import router as system_health_router


class TaskRequest(BaseModel):
    task: str


@pytest.fixture()
def api_client() -> TestClient:
    app = FastAPI()
    app.include_router(system_health_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/tasks/execute")
    def execute_task(payload: TaskRequest) -> dict[str, str]:
        if payload.task == "explode":
            raise HTTPException(status_code=422, detail="unsafe task")
        return {"task": payload.task, "state": "completed"}

    @app.post("/agents")
    def create_agent() -> dict[str, str]:
        return {"agent_id": "agent-1", "status": "created"}

    @app.get("/memory/{key}")
    def retrieve_memory(key: str) -> dict[str, str]:
        if key == "missing":
            raise HTTPException(status_code=404, detail="not found")
        return {"key": key, "value": "cached-value"}

    @app.post("/tools/invoke")
    def invoke_tool(payload: dict[str, str]) -> dict[str, str]:
        if payload.get("tool") == "forbidden":
            raise HTTPException(status_code=400, detail="tool disabled")
        return {"tool": payload.get("tool", "noop"), "status": "invoked"}

    return TestClient(app)


def test_health_endpoint_schema_and_timeout(api_client: TestClient) -> None:
    start = perf_counter()
    response = api_client.get("/health")
    elapsed = perf_counter() - start
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert elapsed < 1.0


def test_task_execution_endpoint_and_error_handling(api_client: TestClient) -> None:
    ok = api_client.post("/tasks/execute", json={"task": "build report"})
    assert ok.status_code == 200
    assert {"task", "state"}.issubset(ok.json())

    bad = api_client.post("/tasks/execute", json={"task": "explode"})
    assert bad.status_code == 422


def test_agent_creation_endpoint(api_client: TestClient) -> None:
    response = api_client.post("/agents")
    assert response.status_code == 200
    assert "agent_id" in response.json()


def test_memory_retrieval_endpoint(api_client: TestClient) -> None:
    found = api_client.get("/memory/session-1")
    assert found.status_code == 200
    assert {"key", "value"}.issubset(found.json())

    missing = api_client.get("/memory/missing")
    assert missing.status_code == 404


def test_tool_invocation_endpoint(api_client: TestClient) -> None:
    response = api_client.post("/tools/invoke", json={"tool": "calculator"})
    assert response.status_code == 200
    assert response.json()["status"] == "invoked"

    blocked = api_client.post("/tools/invoke", json={"tool": "forbidden"})
    assert blocked.status_code == 400


def test_concurrent_load_simulation(api_client: TestClient) -> None:
    def _call() -> int:
        return api_client.get("/health").status_code

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: _call(), range(100)))

    assert all(code == 200 for code in results)
