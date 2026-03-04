# Autonomous Multi-Agent Platform Audit

## Executive Summary
This repository already contains **two agent execution stacks**:
1. A lightweight `apps/orchestrator + apps/executor` pipeline for deterministic objective→task→execution flows.
2. A richer `backend/` AgentOS runtime with multi-node flow execution, CrewAI integration, streaming events, and tool APIs.

The platform is currently best classified as a **multi-agent workflow platform** (not yet a fully autonomous agent platform).

---

## STEP 1 — Repository architecture mapping

### Top-level structure and runtime boundaries

| Directory | Role | Runtime Participation | Boundary |
|---|---|---|---|
| `apps/web` | Next.js frontend with AgentOS canvas UI, auth UX, run controls, streaming UI | Sends run requests to backend, subscribes to websocket events, stores canvas state | **Frontend** |
| `apps/orchestrator` | MVP planning API service | Creates `runs/tasks` from objective and dispatches task execution to executor | **Orchestration (legacy/simple path)** |
| `apps/executor` | MVP task execution service | Clones repos, creates branch, writes notes, computes diff, uploads artifacts | **Execution (legacy/simple path)** |
| `backend/api` | Main runtime API (auth, flows, runs, tools, websocket, metrics) | Entry point for AgentOS flow execution and lifecycle control | **Orchestration/API layer** |
| `backend/orchestrator` | Crew builder, LangGraph stub, event streaming | Compiles flow config to CrewAI run, handles retries/timeouts, emits events to Redis | **Core orchestration runtime** |
| `backend/tools` | External capability adapters (search, browser, travel, finance, calendar, phone, excel) | Exposed via `/api/tools/*` and potentially available to agents | **Tool layer** |
| `backend/db` | Supabase client and audit integrations | Persists flow/execution/history data | **Persistence layer** |
| `backend/models` | Pydantic schemas for flow/event contracts | Governs data contracts across UI/API/runtime | **Contract layer** |
| `prompts` | Prompt engineering templates and examples | Dev-time authoring aid, not runtime execution engine | **Prompt asset library** |
| `packages/shared` | Shared TS package | Shared frontend types/utilities | **Shared dev package** |
| `infra` | Dockerfiles/scripts | Deployment/runtime bootstrapping | **Infrastructure** |
| `docs` | Architecture guidance and roadmap notes | Design-time reference | **Documentation** |

### High-level runtime architecture diagram (text)

```text
[User/UI: apps/web]
   |  POST /api/agents/run
   v
[Backend FastAPI: backend/main.py]
   |-- routes_agents.run_flow -> asyncio task registry + execution row
   |-- orchestrator/crew_builder.build_crew_from_config
   |       -> CrewAI Agent/Task graph (topologically ordered)
   |       -> LLM provider (OpenAI/Anthropic/Ollama)
   |       -> retry/timeout wrappers
   |-- orchestrator/event_stream.publish_event -> Redis Pub/Sub
   |-- websocket /ws/{session_id} -> UI live stream
   |-- routes_history/routes_flows -> Supabase persistence
   |-- routes_tools -> direct tool invocation endpoints

Legacy path in parallel:
[apps/orchestrator] -> deterministic planner -> [apps/executor] -> git clone/diff/artifacts
```

---

## STEP 2 — Agent implementation analysis

### Agent-related components identified
- **Agent definitions/specs**: `backend/agents/*.py` and `backend/agents/base_agent.py` (role/goal/backstory/default tools metadata).
- **Flow/agent schema contracts**: `backend/models/schemas.py` (`FlowConfig`, `NodeConfig`, `AgentType`, `LLMProvider`).
- **Orchestrator/builder**: `backend/orchestrator/crew_builder.py` builds CrewAI `Agent`, `Task`, and `Crew` objects per node.
- **Execution control**: `backend/api/routes_agents.py` starts/cancels runs and tracks running asyncio tasks.
- **Graph orchestration skeleton**: `backend/orchestrator/graph_builder.py` contains a minimal LangGraph passthrough stub.
- **Planner in legacy stack**: `apps/orchestrator/langgraph_planner.py` deterministic template matcher (keyword-based), not a live LLM planner loop.

### How agents are created, configured, and executed
1. UI builds canvas nodes and edges (`apps/web/components/agentos/RunModal.tsx`).
2. Payload maps to `FlowConfig` (`backend/models/schemas.py`).
3. `/api/agents/run` stores execution row and spins async run task (`backend/api/routes_agents.py`).
4. Runtime topologically sorts nodes and creates CrewAI agents/tasks (`backend/orchestrator/crew_builder.py`).
5. Crew executes sequentially (`Process.sequential`) and emits events (`orchestrator/event_stream.py`).
6. Websocket streams events to UI (`backend/api/websocket.py`).

### Agent maturity classification in this codebase
- **A) Prompt personas**: yes (agent prompts/system_prompt and role metadata).
- **B) Workflow agents**: yes (flow DAG + sequential crew execution).
- **C) Semi-autonomous agents**: partially (retry/timeouts/cancellation and multi-agent orchestration).
- **D) Autonomous agents**: no (no persistent self-directed objective loop, no autonomous task generation).

---

## STEP 3 — Execution loop analysis

### Loops/schedulers/workers present
- **Retry loop** with exponential backoff for task execution wrapper in `crew_builder._wrap_task_execution`.
- **DAG ordering loop** (`topological_sort`) ensuring acyclic execution order.
- **Async run loop orchestration** via `asyncio.create_task` and in-memory run registries (`RUNNING_EXECUTIONS`, `CANCEL_FLAGS`).
- **Background task execution** in legacy executor via FastAPI `BackgroundTasks` (`apps/executor/main.py`).

### Missing autonomous loop capabilities
- No goal-reassessment loop after execution completion.
- No recursive replanning where failures generate new strategies automatically.
- No dynamic task spawning/subagent creation from runtime outcomes.
- No persistent scheduler-driven objective queue (despite Celery app being configured, no production task graph appears wired to it).

### Limitation summary
Current execution is **session-triggered, bounded, and finite** per user request; it is not a continuous autonomous lifecycle.

---

## STEP 4 — Tooling capabilities

### Implemented tool integrations
- Web search (`backend/tools/search_tools.py`, Tavily).
- Browser automation/content extraction + travel search (`backend/tools/browser_tools.py`, Playwright + OSM APIs).
- Spreadsheet generation (`backend/tools/excel_tools.py`).
- Finance data (`backend/tools/finance_tools.py`, yfinance).
- Calendar (`backend/tools/calendar_tools.py`, Google Calendar or simulation fallback).
- Phone (`backend/tools/phone_tools.py`, Twilio or simulation fallback).
- Tool API routes (`backend/api/routes_tools.py`).

### Are tools wired into agent runtime?
- **Partially, mostly no for autonomous path.** In `crew_builder.py`, `_resolve_tools()` currently returns `[]`, and agents are instantiated with `tools=[]`. This means agents in Crew execution cannot actively call these tools despite tool modules existing.
- Tools are reliably callable via dedicated API endpoints (`/api/tools/*`), but not yet bound as runtime callable tool objects for CrewAI agents.

---

## STEP 5 — Memory architecture

### Existing memory/history
- **Execution/event history** persisted in `public.executions` and exposed by `/api/history`.
- **Flow persistence** in `public.flows`.
- **Audit logs** in `public.audit_logs`.
- CrewAI is configured with `memory=True` in `Crew(...)`, which provides runtime memory behavior within the crew context.

### Missing memory layers
- No explicit long-term semantic memory subsystem (no embeddings pipeline, no retrieval orchestrator, no vector query path in runtime).
- No per-agent memory profiles with episodic + semantic separation.
- No durable memory write/read loop tied to task outcomes.

### Conclusion
Memory exists as **execution history and transient runtime context**, not as a full autonomous long-term agent memory architecture.

---

## STEP 6 — Runtime orchestration lifecycle

### Actual lifecycle (current)

```text
User objective (UI modal)
  -> Flow payload (nodes, edges, inputs)
  -> /api/agents/run
  -> Persist execution row
  -> Build Crew from FlowConfig (topological node ordering)
  -> Sequential kickoff (LLM calls)
  -> Emit events to Redis
  -> Stream to websocket UI
  -> Persist final status/result/events
```

### Orchestration type
- **Static + deterministic structure** at graph level (user-defined nodes/edges).
- **LLM-driven inside each node task**.
- **Bounded feedback** (retry and cancellation), but no long-term autonomous feedback loop.

---

## STEP 7 — Autonomy evaluation

### Scale result
**Level 2 — Multi-agent workflow engine**

Why not Level 3/4:
- No self-generated objective backlog.
- No persistent autonomous planner loop.
- No dynamic subtask spawning and reassignment loop.
- Tool invocation not integrated into core agent runtime path.

---

## STEP 8 — Architectural gaps to reach full autonomy

Key missing capabilities:
1. **Continuous goal evaluation loop** (daemon/scheduler that re-checks objective status).
2. **Autonomous planning cycles** (plan -> execute -> evaluate -> replan).
3. **Task self-generation** from observations/errors.
4. **Persistent long-term memory** (vector + episodic + structured world state).
5. **Agent-to-agent communication protocol** (beyond sequential Crew callbacks).
6. **Robust scheduling/background autonomy** (cron/event triggers, durable queue, retries, dead-letter).
7. **Feedback learning loops** (policy/performance adaptation).
8. **Runtime tool binding** (tools callable directly from agent reasoning).
9. **Long-horizon planning primitives** (milestones, dependencies, budget/time governors).

---

## STEP 9 — Next-generation architecture proposal

### Target architecture: Autonomous Agent Runtime

```text
[Goal Manager]
   -> evaluates active goals continuously
   -> emits planning jobs

[Planner Service]
   -> decomposes goal into milestone DAG
   -> writes task graph to Task Store

[Collaboration Engine]
   -> assigns tasks to agent pools
   -> brokered agent-to-agent messages

[Agent Runtime]
   -> think/act loop per agent
   -> bound tool adapters
   -> memory read/write hooks

[Tool Gateway]
   -> typed tools + auth + quotas + telemetry

[Memory System]
   -> short-term session memory
   -> long-term episodic store
   -> vector semantic store (RAG)

[Scheduler + Queue]
   -> delayed tasks, recurring goals, retries, DLQ

[Evaluator/Critic]
   -> validates outputs vs success criteria
   -> triggers replan or human approval
```

### Autonomous loop pseudocode

```python
while True:
    goals = goal_store.fetch_active_goals()
    for goal in goals:
        state = memory.load_goal_state(goal.id)
        if evaluator.is_goal_satisfied(goal, state):
            goal_store.mark_done(goal.id)
            continue

        if planner.needs_replan(goal, state):
            dag = planner.generate_dag(goal, state)
            task_store.upsert_dag(goal.id, dag)

        ready_tasks = task_store.get_ready_tasks(goal.id)
        for task in ready_tasks:
            agent = collaboration.assign_agent(task)
            result = agent_runtime.execute(task, tools=tool_gateway, memory=memory)
            memory.append_episode(goal.id, task.id, result)
            evaluator.record(task, result)
            task_store.advance(task.id, result)

    scheduler.sleep_tick()
```

### Agent communication protocol (example)
- Envelope: `{message_id, goal_id, task_id, from_agent, to_agent, intent, payload, requires_ack, timestamp}`
- Intents: `request_context`, `delegate_subtask`, `deliver_result`, `escalate_risk`, `request_approval`.
- Transport: Redis Streams / NATS / Kafka (with persistence + replay).

---

## STEP 10 — Concrete code-level transformation plan (Agent OS)

### A. New modules to add
1. `backend/autonomy/goal_manager.py`
   - Continuous scanner of active goals and status checks.
2. `backend/autonomy/planner.py`
   - LLM-driven planner with structured DAG output + validation.
3. `backend/autonomy/scheduler.py`
   - Cron-like and event-driven dispatcher backed by Celery/Redis.
4. `backend/autonomy/collaboration.py`
   - Agent messaging and delegation protocol.
5. `backend/memory/store.py`
   - Unified memory interface (episodic, semantic, working memory).
6. `backend/memory/vector_index.py`
   - Embedding + retrieval adapter (Chroma/pgvector).
7. `backend/tools/runtime_registry.py`
   - Typed runtime tool registry binding IDs to callables.
8. `backend/evaluation/critic.py`
   - Output scorer and replanning trigger logic.

### B. Existing modules to modify
1. `backend/orchestrator/crew_builder.py`
   - Replace `_resolve_tools()` stub with real tool binding.
   - Inject memory hooks pre/post task execution.
   - Add branch logic for parallel task execution where graph allows.
2. `backend/api/routes_agents.py`
   - Route `/run` should enqueue durable jobs instead of in-process-only tasks.
   - Add `/goals/*` endpoints for persistent autonomous goals.
3. `backend/main.py`
   - Wire scheduler startup lifecycle and background daemons.
4. `backend/db/schema.sql`
   - Add tables: `goals`, `goal_cycles`, `agent_messages`, `memory_episodes`, `memory_embeddings`, `scheduled_jobs`, `task_queue`.
5. `apps/web`
   - Add Goal Console: active goals, confidence, blockers, next planned actions.

### C. Execution loop implementation blueprint

```python
def autonomous_tick(goal_id: str):
    goal = goals.get(goal_id)
    context = memory.compose_context(goal_id)

    plan = planner.plan_or_replan(goal, context)
    for task in plan.ready_tasks:
        assigned = collaboration.assign(task)
        result = runtime.execute(assigned, context)
        memory.persist(task, result)
        critic.evaluate(task, result)
        if critic.requires_replan(task, result):
            planner.flag_replan(goal_id)
```

### D. Scheduler integration
- Use Celery Beat (or APScheduler) for periodic objective review and maintenance tasks.
- Use Celery workers for execution and a dead-letter queue for failed tasks.
- Store all run states durably in DB to survive process restarts.

### E. Tool binding design
- Map `tool_id -> ToolSpec(name, input_schema, call, timeout, retry_policy, auth_scope)`.
- Expose tool health and usage telemetry in `metrics_store`.
- Enforce policy guardrails (rate limits, allowed domains, PII controls).

### F. Memory integration design
- Working memory: Redis keyed by `session_id/goal_id`.
- Episodic memory: Postgres `memory_episodes` table.
- Semantic memory: Chroma or pgvector index with retrieval by intent/task.

---

## STEP 11 — Final classification

## **Final classification: Multi-agent workflow platform (approaching Agent OS foundation, but not autonomous yet).**

### Evidence from repository
- Multi-agent orchestration exists (`backend/orchestrator/crew_builder.py`, `backend/api/routes_agents.py`).
- Graph orchestration for advanced state is currently stubbed (`backend/orchestrator/graph_builder.py`).
- Tool integrations exist but runtime binding is incomplete (`backend/tools/*` vs `_resolve_tools() -> []`).
- Execution remains user-triggered finite sessions (`apps/web/components/agentos/RunModal.tsx`, `/api/agents/run`).
- Legacy deterministic planner/executor stack reinforces workflow-first model (`apps/orchestrator/langgraph_planner.py`, `apps/executor/runner.py`).

---

## Engineering Recommendations (prioritized)
1. **P0:** Wire runtime tools into agent execution path and add typed registry.
2. **P0:** Introduce durable scheduler/queue-driven run engine (Celery tasks actually used).
3. **P0:** Implement autonomous goal loop with replan/evaluate cycle.
4. **P1:** Add persistent memory architecture (episodic + semantic).
5. **P1:** Add agent communication/delegation protocol and message bus.
6. **P1:** Add evaluator/critic module for quality gates and self-correction.
7. **P2:** Add policy/risk controls (budget, tool permissions, human approval checkpoints).
8. **P2:** Expand UI from run-centric to goal-centric operations dashboard.
