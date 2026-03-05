# Massively Scalable Agent Runtime Architecture

## Target outcomes

- 10,000 concurrent agents with bounded fan-out and predictable queue pressure.
- Controlled token and cost burn through dynamic scheduling and governance limits.
- Horizontal scalability through partitioned queues and stateless workers.
- Resilience to worker crashes by externalizing state and using durable stores.

## System architecture diagram

```text
                         +----------------------------+
                         |    Coordinator Agents      |
                         | goal planning + aggregation|
                         +-------------+--------------+
                                       |
                                       v
+-------------------+      +-------------------------+      +------------------------+
| Spawn Controller  |----->| Partitioned Task Queue  |<-----| Autoscaler + Load Mgr |
| global/rate/depth |      | tenant|goal|priority    |      | worker fleet scaling   |
+---------+---------+      +-----------+-------------+      +-----------+------------+
          |                            |                                  |
          v                            v                                  v
+-------------------+      +-------------------------+      +------------------------+
| Lifecycle Manager |      | Stateless Worker Pool   |      | Utility Agents         |
| state + idle kill |      | tool calls + execution  |      | validate/summarize/eval|
+---------+---------+      +-----------+-------------+      +-----------+------------+
          |                            |                                  |
          +---------------+------------+------------------+---------------+
                          |                               |
                          v                               v
               +---------------------+        +--------------------------+
               | Token Budget Sched. |        | Cost Governor            |
               | agent/tenant/global |        | llm/tool/compute limits  |
               +-----------+---------+        +------------+-------------+
                           |                               |
                           +--------------+----------------+
                                          v
                            +----------------------------+
                            | Monitoring + Tracing + SLO |
                            +----------------------------+
```

## Agent hierarchy model

### Coordinator agents
- Plan goals into executable tasks.
- Spawn worker tasks through controlled interfaces.
- Aggregate and publish final outputs.

### Worker agents
- Execute concrete tasks and invoke tools.
- Perform local reasoning.
- **Cannot spawn unlimited workers** because all spawn requests pass through `SpawnController` and recursion depth limits.

### Utility agents
- Validation of outputs.
- Summarization and compression of large result sets.
- Evaluation and scoring loops.

## Spawn control strategy

`SpawnController` enforces:

- `max_agents_global`
- `max_agents_per_goal`
- `max_spawn_per_minute`
- `max_recursion_depth`

On violations, spawn requests are queued instead of immediately creating agents. This converts failure modes from runaway explosion to controlled backlog.

## Token budget design

`TokenBudgetScheduler` tracks:

- Per-agent token usage.
- Per-tenant token usage.
- Global token usage.

Actions:

- Pause non-critical agents on global exhaustion.
- Delay tasks for over-budget agents/tenants.
- Continue critical-only paths when configured.

## Worker scaling strategy

- Workers are stateless (`workers/stateless_worker.py`).
- Durable state exists only in task store, memory store, and event bus.
- Workers subscribe to queue partitions (`tenant`, `goal`, `priority`) to avoid global queue contention.
- Horizontal autoscaling adds/removes workers by partition demand and queue depth.

## Cost governance model

`CostGovernor` tracks:

- LLM spend
- Tool spend
- Compute spend

Limits are applied per user, per tenant, and per execution. Enforcement can block or defer runtime actions before budget overruns cascade.

## Model pooling and routing

`llm/model_pool.py` provides:

- Connection pooling across model tiers.
- Request batching per tier.
- Routing policy:
  - simple tasks -> fast model
  - medium tasks -> balanced model
  - complex reasoning -> high reasoning model

This controls latency and keeps premium model usage for only high-value tasks.

## Stability at massive scale

The stress suite simulates 100, 1,000, and 5,000-agent scenarios and records:

- latency
- queue depth
- worker utilization
- token consumption

The architecture is designed to scale to 10,000 concurrent agents by combining fan-out control, partitioned work distribution, stateless execution, and budget-aware scheduling.
