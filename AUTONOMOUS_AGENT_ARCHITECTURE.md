# AUTONOMOUS AGENT PLATFORM

## System architecture
The platform now operates as an **AUTONOMOUS AGENT PLATFORM** built around:
- Runtime agent/tool composition in `backend/orchestrator/crew_builder.py` + `backend/tools/runtime_tools.py`.
- A continuous autonomous loop in `backend/autonomy/agent_loop.py`.
- Persistent memory backed by ChromaDB in `backend/memory/vector_memory.py`.
- Dynamic task queuing in `backend/orchestrator/task_queue.py`.
- Agent communication through `backend/agents/communication_bus.py`.
- Goal evaluation in `backend/goals/goal_manager.py`.
- Periodic scheduling in `backend/scheduler/agent_scheduler.py`.

## Agent lifecycle
1. Flow request enters `/api/agents/run`.
2. Agents are instantiated from canvas config.
3. Tools are resolved dynamically and bound per agent.
4. Autonomous loop starts and repeats until completion or guardrail stop.
5. Goal state and execution outputs are persisted.
6. Loop exits safely when constraints are reached.

## Tool system
- `resolve_tools(agent_config)` maps declared tool IDs + core runtime tools.
- Supported categories:
  - web search
  - browser automation
  - filesystem access
  - API calls
  - database queries
  - domain-specific finance/excel/travel tools

## Memory system
`VectorMemory` stores and retrieves:
- previous plans and events (`store_event`)
- task outputs (`store_task_result`)
- environment knowledge / history (`retrieve_context`, `semantic_search`)

Persistence is local-disk Chroma (`PersistentClient`).

## Autonomous execution loop
`AutonomousAgentLoop.run()` performs:
1. evaluate current memory context
2. plan new tasks
3. execute queue
4. review via goal manager
5. update memory and cost

Guardrails:
- `max_iterations`
- `max_runtime_seconds`
- `max_cost`
- safe stop with status `stopped`

## Scheduler system
`AgentScheduler` supports periodic autonomous execution:
- run every X minutes
- queue periodic jobs
- start/stop background scheduler

## Communication and delegation
`CommunicationBus` enables:
- `send_message(agent_id, payload)`
- `broadcast_event(event)`
- mailbox-style receive for collaboration

Dynamic task spawning/delegation is supported through `spawn_tasks` and `delegate_to` payload fields in queued tasks.
