# Agentic Dev Studio (MVP)

A commercial-grade monorepo for an AI-powered development studio.

## Architecture
- **apps/web**: Next.js 14+ (App Router), Tailwind CSS, shadcn/ui, Supabase Auth.
- **apps/orchestrator**: Python FastAPI service that plans runs using a Mock LangGraph agent.
- **apps/executor**: Python FastAPI service that clones repos, executes tasks, and produces patches/artifacts.
- **packages/shared**: Shared TypeScript types.
- **Database**: Supabase Postgres (Direct connection).

## Setup Instructions

### 1. Database & Auth (Supabase)
- Create a new Supabase project.
- Run the contents of `schema.sql` in the Supabase SQL Editor to create the necessary tables.
- Enable Email/Password auth in the Supabase Dashboard (Authentication > Providers).
- Create a storage bucket named `artifacts` and set it to public (or add appropriate RLS policies).

### 2. Environment Variables
Copy `.env.example` to `.env` in the root and fill in your values:
```bash
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

### 3. Install Dependencies
```bash
pnpm install
```

### 4. Running the Services
Run each of these in a separate terminal:

**Web App:**
```bash
cd apps/web
pnpm dev
```

**Orchestrator:**
```bash
cd apps/orchestrator
./run.sh
```

**Executor:**
```bash
cd apps/executor
./run.sh
```

## Quick Demo Flow
1. **Login**: Go to `http://localhost:3000/login` and sign up/in.
2. **Connection**: Go to the **Connections** page and paste a GitHub Personal Access Token (PAT).
3. **Project**: Go to **Projects**, create a new project with a valid GitHub Repo URL.
4. **Run**: Click on the project, and in the "Start New Run" form, enter an objective (e.g., "Add a feature and generate an xlsx report").
5. **Execute**: You will be redirected to the Run Detail page. Select a task and click **Execute Task**.
6. **Results**: Watch the logs stream in. Once finished, you'll see the **Proposed Changes (Diff)** and any generated **Artifacts** for download.

## TODO (Commercial Path)
- [ ] Implement actual LLM logic in `apps/orchestrator/langgraph_planner.py`.
- [ ] Encrypt GitHub tokens at rest.
- [ ] Implement true SSE/WebSockets for logs instead of polling.
- [ ] Add Docker-based sandbox execution for the Executor.
- [ ] Add RLS policies for multi-tenancy.
