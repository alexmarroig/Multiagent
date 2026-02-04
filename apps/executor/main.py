from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .db import get_db
from .runner import run_task_job

app = FastAPI(title="Agentic Dev Studio - Executor")

class JobRequest(BaseModel):
    task_id: str

@app.post("/jobs/execute-task")
async def execute_task(req: JobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(run_task_job, db, req.task_id)
    return {"status": "queued", "task_id": req.task_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
