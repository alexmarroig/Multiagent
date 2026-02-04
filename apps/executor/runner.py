import os
import subprocess
import shutil
from sqlalchemy.orm import Session
from .models import Task, Run, Project, Connection, TaskLog, Artifact
from supabase import create_client, Client

def log_to_db(db: Session, task_id: str, line: str):
    new_log = TaskLog(task_id=task_id, line=line)
    db.add(new_log)
    db.commit()
    print(line)

def run_task_job(db: Session, task_id: str):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task: return

    run = db.query(Run).filter(Run.id == task.run_id).first()
    project = db.query(Project).filter(Project.id == run.project_id).first()
    connection = db.query(Connection).filter(Connection.user_id == project.user_id, Connection.type == 'github').first()

    token = connection.token if connection else None
    repo_url = project.repo_url
    if token and "github.com" in repo_url:
        repo_url = repo_url.replace("https://", f"https://x-access-token:{token}@")

    work_dir = f"/tmp/ads-{task_id}"
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    try:
        task.status = "running"; db.commit()
        log_to_db(db, task_id, f"Cloning repository: {project.repo_url}")
        subprocess.run(["git", "clone", repo_url, "repo"], cwd=work_dir, check=True, capture_output=True)
        repo_path = os.path.join(work_dir, "repo")
        subprocess.run(["git", "checkout", project.default_branch], cwd=repo_path, check=True, capture_output=True)

        new_branch = f"task-{task_id[:8]}"
        subprocess.run(["git", "checkout", "-b", new_branch], cwd=repo_path, check=True, capture_output=True)

        # Work
        notes_path = os.path.join(repo_path, "TASK_NOTES.md")
        with open(notes_path, "a") as f:
            f.write(f"\n## Task: {task.title}\nDescription: {task.description}\n")

        if "xlsx" in task.title.lower() or "planilha" in task.title.lower():
            from .xlsx import create_basic_xlsx
            xlsx_filename = f"report-{task_id[:8]}.xlsx"
            xlsx_path = create_basic_xlsx(xlsx_filename, task.title, task.description or "")
            log_to_db(db, task_id, f"Generated artifact: {xlsx_filename}")

            storage_path = f"{task_id}/{xlsx_filename}"
            artifact = Artifact(task_id=task_id, name=xlsx_filename, type="xlsx", storage_path=storage_path)
            db.add(artifact); db.commit()
            upload_to_supabase(xlsx_path, storage_path)

        diff_res = subprocess.run(["git", "diff", project.default_branch], cwd=repo_path, check=True, capture_output=True, text=True)
        task.patch = diff_res.stdout
        task.status = "completed"; db.commit()
        log_to_db(db, task_id, "Task completed successfully.")
    except Exception as e:
        log_to_db(db, task_id, f"Error: {str(e)}")
        task.status = "failed"; db.commit()

def upload_to_supabase(local_path, remote_path):
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key: return
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        with open(local_path, "rb") as f:
            supabase.storage.from_("artifacts").upload(remote_path, f, {"upsert": "true"})
    except Exception as e:
        print(f"Upload failed: {e}")
