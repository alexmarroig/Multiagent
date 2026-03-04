# AgentOS Architecture

## Classification

**AUTONOMOUS AGENT OPERATING SYSTEM**

## System Architecture

The platform is structured around a central runtime (`core/agent_runtime.py`) that governs lifecycle, budget control, and health visibility for all agents. The runtime executes the autonomy loop (`core/autonomy_loop.py`) in cycles and enforces explicit cost guardrails.

Supporting subsystems:

- **Tool Layer**: `tools/tool_registry.py` centralizes dynamic tool registration and attaches tool handles to agents at runtime.
- **Memory Layer**: `memory/vector_memory.py` stores results, decisions, knowledge, and environment snapshots with embedding-backed semantic retrieval.
- **Coordination Layer**: `communication/message_bus.py` enables direct messaging, event broadcast, and task delegation.
- **Execution Layer**: `tasks/task_graph.py` supports dependency-aware task execution with dynamic spawning, priorities, and parallel dispatch.
- **Control Layer**: `scheduler/agent_scheduler.py` handles periodic jobs, goal monitoring, restart hooks, and background execution.

## Agent Lifecycle

1. Runtime initializes baseline agent profiles.
2. Tools are registered and attached according to each agent's role.
3. Runtime executes autonomy cycles.
4. Runtime resolves skill gaps and dynamically spawns specialized agents when required.
5. Runtime continuously monitors cost, errors, and health.
6. Runtime degrades/stops safely when guardrails are hit.

## Task Graph Engine

The task graph supports:

- **Dependencies**: tasks only become ready after parent tasks complete.
- **Dynamic Spawning**: downstream tasks can be emitted during execution.
- **Priority Queues**: lower priority score executes first.
- **Parallel Execution**: ready tasks can run via thread pool workers.

## Memory System

Vector memory stores:

- task results
- agent decisions
- durable knowledge
- environment state snapshots

Planners query semantic memory before plan generation to provide historical context, reducing repeated failure patterns and improving long-horizon continuity.

## Tool Registry

The registry includes first-class support for:

- web search
- browser automation
- filesystem access
- API execution
- database queries
- code execution

All tools are registered centrally and can be attached dynamically to newly spawned agents.

## Communication Bus

Message bus capabilities:

- point-to-point messaging
- system-wide event broadcast
- task delegation payloads between agents

This enables multi-agent collaboration patterns rather than isolated worker execution.

## Scheduler

The scheduler executes autonomous control-plane jobs including:

- periodic tasks
- goal monitoring
- automated agent restart checks
- continuous background execution loops
