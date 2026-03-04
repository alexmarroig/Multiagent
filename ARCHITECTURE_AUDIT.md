# Deep Architectural Audit

## Scope
Repository: `Multiagent`
Goal: classify whether implementation is an autonomous AI agent system or primarily prompt templates.

## 1) Repository architecture map

### Root directories
- `.github/`: CI workflow definitions.
- `apps/`: monorepo app layer.
  - `apps/web/`: Next.js frontend (AgentOS canvas, auth, run UI, API proxy routes).
  - `apps/orchestrator/`: lightweight FastAPI planner service; generates deterministic task lists from objectives and dispatches tasks to executor.
  - `apps/executor/`: lightweight FastAPI executor service; clones repos, writes task notes, optionally generates XLSX artifact, stores patch.
- `backend/`: larger FastAPI backend with CrewAI-based flow execution, flow CRUD, auth, tools endpoints, websocket stream, observability, and DB schema.
- `docs/`: architectural documentation and roadmap.
- `infra/`: Dockerfiles/scripts for orchestrator/executor runtime.
- `packages/shared/`: shared TypeScript contracts.
- `prompts/`: prompt-template library (frontend/backend/infra prompt patterns and examples).
- `scripts/`: helper scripts (e.g., admin seeding).

## 2) Agent implementation findings

### Concrete agent-related code exists
- `backend/agents/*.py` defines agent specs (roles/goals/backstory/default tools).
- `backend/orchestrator/crew_builder.py` dynamically builds CrewAI `Agent`, `Task`, and `Crew` objects from canvas node config.
- `backend/models/schemas.py` defines `FlowConfig`, `NodeConfig`, agent/provider enums.

### Also present: simplified "planner/executor" pair
- `apps/orchestrator/langgraph_planner.py` is deterministic keyword-based planning (no true LLM planning loop).
- `apps/orchestrator/main.py` stores runs/tasks then calls executor API endpoint.
- `apps/executor/main.py` queues execution via FastAPI background task.

## 3) Execution loop detection

### Present loops/mechanisms
- Task retry loop with backoff and timeout wrapper in `backend/orchestrator/crew_builder.py` (`for attempt ...`).
- Topological sort loop (`while ready`) for DAG execution ordering.
- Async execution task management in `backend/api/routes_agents.py` using `asyncio.create_task`, cancellation flags, running-task registry.
- Background worker style in `apps/executor/main.py` via `BackgroundTasks.add_task(run_task_job, ...)`.

### Not found
- No recursive self-spawn loop where agents autonomously create/subdivide new tasks in persistent queue.
- No planner->executor iterative re-plan loop in `apps/orchestrator` (single-shot plan generation).
- Celery configured in `backend/main.py` and docker-compose worker, but no declared Celery tasks found.

## 4) Tool integrations

### Implemented tool modules/endpoints
- Web search via Tavily (`backend/tools/search_tools.py`).
- Browser/navigation and travel search (Playwright + OpenStreetMap APIs) (`backend/tools/browser_tools.py`).
- Calendar integration (Google Calendar API with dev simulation fallback) (`backend/tools/calendar_tools.py`).
- Phone integration (Twilio with dev simulation fallback) (`backend/tools/phone_tools.py`).
- Finance data (yfinance) (`backend/tools/finance_tools.py`).
- Excel generation/download endpoints (`backend/api/routes_tools.py`, `backend/tools/excel_tools.py`).

### Critical runtime limitation
- In Crew builder, tool resolution currently returns an empty list and agents are instantiated with `tools=[]`; therefore tools are not actually wired into autonomous agent task execution path.

## 5) Autonomy level evaluation

- User prompts/objectives are required from UI (`RunModal` requires objective and sends flow payload).
- System executes multi-step tasks in sequence (Crew sequential process, orchestrator-generated task list, executor jobs).
- No evidence of autonomous task spawning/subtask generation by runtime.
- Cancellation, streaming, and execution status exist, but autonomy is orchestrated by user-triggered sessions.

## 6) Runtime architecture (text diagram)

```mermaid
flowchart LR
  U[User in Next.js UI] -->|POST /api/agents/run| B[backend FastAPI]
  B -->|build_crew_from_config| C[CrewAI sequential run]
  C -->|LLM calls| L[(OpenAI/Anthropic/Ollama)]
  C -->|events| R[(Redis Pub/Sub)]
  R --> W[WebSocket /ws/{session_id}]

  U -->|legacy path /runs| O[apps/orchestrator FastAPI]
  O --> P[deterministic planner]
  O -->|POST /jobs/execute-task| E[apps/executor FastAPI]
  E --> G[git clone + branch + notes + diff]
  E --> S[(Supabase artifacts/logs)]

  B --> D[(Supabase)]
  B --> T[/api/tools endpoints]
```

## 7) Final classification

**Classification: Multi-agent workflow system (not a fully autonomous agent platform).**

Rationale:
1. There is real multi-agent orchestration infrastructure (CrewAI agents/tasks, DAG ordering, execution lifecycle, event streaming).
2. Runs are user-triggered and objective-driven, with no persistent autonomous planning loop.
3. Tool modules exist, but tool wiring into agent runtime is currently incomplete (`tools=[]` in crew runtime path).
4. Repository also includes a significant prompt-template library (`prompts/`), but it is not the only functionality.

Secondary note:
- `apps/orchestrator` appears MVP/legacy and deterministic, while `backend/` is the richer agent runtime path. The coexistence suggests transition architecture rather than a unified autonomous platform.
