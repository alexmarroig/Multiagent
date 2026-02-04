from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import os, requests
from .db import get_db
from .models import Run, Task
from .langgraph_planner import generate_plan
from pydantic import BaseModel

app = FastAPI(title="Agentic Dev Studio - Orchestrator")
EXECUTOR_URL = os.getenv("EXECUTOR_URL", "http://localhost:8002")

class RunCreate(BaseModel):
    project_id: str
    objective: str

@app.post("/runs")
async def create_run(run_data: RunCreate, db: Session = Depends(get_db)):
    run = Run(project_id=run_data.project_id, objective=run_data.objective, status="planning")
    db.add(run)
    db.commit()
    db.refresh(run)

    plan_md, tasks_data, chat_log = generate_plan(run_data.objective)
    run.plan = plan_md
    run.chat_history = chat_log
    run.status = "pending"
    db.commit()

    for t in tasks_data:
        task = Task(
            run_id=run.id,
            title=t["title"],
            description=t["description"],
            order_index=t["order_index"],
            status="todo"
        )
        db.add(task)

    db.commit()
    return {"run_id": str(run.id)}

@app.post("/tasks/{task_id}/execute")
async def execute_task(task_id: str, db: Session = Depends(get_db)):
    try:
        response = requests.post(f"{EXECUTOR_URL}/jobs/execute-task", json={"task_id": task_id})
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
