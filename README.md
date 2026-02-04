# Agentic Dev Studio (MVP) - Powered by ChatDev Logic

A commercial-grade monorepo for an AI-powered development studio, inspired by the **ChatDev** multi-agent framework.

## Architecture
- **apps/web**: Next.js 14+ (App Router), Tailwind CSS, shadcn/ui, Supabase Auth.
- **apps/orchestrator**: Python FastAPI service that simulates a **CEO/CTO/Programmer/Reviewer** workflow for planning.
- **apps/executor**: Python FastAPI service that clones repos, executes tasks, and produces patches/artifacts.
- **packages/shared**: Shared TypeScript types.
- **Database**: Supabase Postgres (Direct connection).

---

## Detailed Supabase Setup Guide

To get this app running, you need to configure your Supabase project as follows:

### 1. Database Schema
1. Open your Supabase Dashboard.
2. Go to the **SQL Editor** in the left sidebar.
3. Click **New Query**.
4. Copy the entire contents of the `schema.sql` file from this repository and paste it into the editor.
5. Click **Run**. This will create all necessary tables: `projects`, `runs`, `tasks`, `artifacts`, `connections`, and `task_logs`.

### 2. Authentication
1. Go to **Authentication** > **Providers**.
2. Ensure **Email** is enabled.
3. (Optional) Disable "Confirm Email" if you want to test immediately with dummy accounts.

### 3. Storage
1. Go to **Storage**.
2. Create a **New Bucket** named `artifacts`.
3. Make it **Public** (or set up a policy to allow authenticated uploads/downloads).

### 4. API Keys & Connection String
1. Go to **Project Settings** > **API**.
    - Copy the `Project URL` -> `SUPABASE_URL`
    - Copy the `anon public` key -> `SUPABASE_ANON_KEY`
    - Copy the `service_role` key -> `SUPABASE_SERVICE_ROLE_KEY`
2. Go to **Project Settings** > **Database**.
    - Under **Connection string**, select **URI**.
    - Copy the URI. It will look like `postgresql://postgres:[YOUR-PASSWORD]@db.[REF].supabase.co:5432/postgres`.
    - Replace `[YOUR-PASSWORD]` with the password you set when creating the project. This is your `DATABASE_URL`.

---

## Environment Variables
Create a `.env` file in the root directory (based on `.env.example`):

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Backends
ORCHESTRATOR_URL=http://localhost:8001
EXECUTOR_URL=http://localhost:8002
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:8001
NEXT_PUBLIC_EXECUTOR_URL=http://localhost:8002
```

---

## Running Locally

1. **Install Dependencies**:
   ```bash
   pnpm install
   ```

2. **Start Services** (Separate terminals):
   - **Web**: `cd apps/web && pnpm dev`
   - **Orchestrator**: `cd apps/orchestrator && ./run.sh`
   - **Executor**: `cd apps/executor && ./run.sh`

---

## ChatDev Multi-Agent Workflow
When you start a "Run", the Orchestrator simulates a collaboration between:
- **CEO**: Defines the vision.
- **CTO**: Breaks it down into architecture tasks.
- **Programmer**: Executes the code changes in the repository.
- **Reviewer**: Generates the final diff and ensures quality.

You can see these roles assigned to tasks in the Run Detail view.
