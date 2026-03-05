# Agent System Safety Layer

This document defines a safety layer that prevents swarm collapse, runaway cost, infinite loops, and unstable behavior in a large-scale autonomous multi-agent platform.

## 1) Agent Admission Control (`core/agent_admission_controller.py`)

The admission controller provides startup safety gates before any agent enters execution.

### Guardrails
- **Concurrent agent limit**: caps active agents globally.
- **Spawn rate per tenant**: limits tenant-level starts per rolling minute.
- **Global spawn burst limit**: caps starts over a short rolling burst window.

### Behavior
- If a request breaches any limit, the request is **queued**.
- As agents complete, queued requests are retried FIFO with fairness rotation.

## 2) Planning Loop Guard (`core/planning_guard.py`)

The planning guard detects non-progressing thought/planning patterns.

### Stops
- **Infinite reasoning loops** via maximum planning depth.
- **Repeated planning cycles** by repeated signature detection.
- **Reflection loops without progress** by tracking non-progress streaks.

### Action
- Exceeding thresholds returns a termination signal and reason.

## 3) Swarm Collapse Prevention (`core/swarm_stability_controller.py`)

The swarm stability controller monitors leading collapse indicators.

### Signals
- Agent spawn rate.
- Task queue growth rate.
- Worker saturation.

### Stabilization Response
When instability is detected:
- **Pause new spawns**.
- **Prioritize active/in-flight tasks**.

## 4) LLM Request Governor (`core/llm_request_governor.py`)

The request governor enforces hard limits to bound cost and latency spikes.

### Controls
- Max requests per minute per agent.
- Max tokens per task.
- Max tokens per tenant (hourly budget).

### Outcomes
- Returns `allow`, `delay:<reason>`, or `reject:<reason>`.

## 5) Semantic LLM Cache (`core/semantic_cache.py`)

The semantic cache reuses prior LLM responses for similar prompts.

### Design
- Stores prompt, response, embedding.
- Uses cosine similarity against cache entries.
- Returns cached response when threshold is met.

### Benefit
- Reduces repeated token spend and median response latency.

## 6) Agent Kill Switch (`core/agent_kill_switch.py`)

Emergency control plane for active incidents.

### Capabilities
- Terminate by agent ID.
- Terminate all agents in a tenant.
- Global emergency stop.

## 7) Safety Metrics (`core/safety_metrics.py`)

The safety layer publishes and alerts on:
- `agent_spawn_rate`
- `planning_loop_depth`
- `queue_growth_rate`
- `token_consumption_rate`

Threshold breaches produce alert strings consumable by monitoring systems.

## 8) Stability Testing (`tests/stability/`)

Stress scenarios validate damping and recovery behavior:
- 1000-agent spawn burst.
- LLM failure cascade / budget breach.
- Queue overload instability detection.
- Planner infinite loop termination.

All scenarios verify defensive controls engage and prevent unbounded instability.
