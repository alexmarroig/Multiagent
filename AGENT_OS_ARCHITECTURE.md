# AGENT_OS_ARCHITECTURE

## 1) Objective

This architecture defines a **production-grade Agent Operating System (Agent OS)** that supports:

- distributed workers
- durable task graphs
- hierarchical supervision
- adaptive scheduling
- human-in-the-loop governance
- guardrails and cost controls

The design is modular and maps directly to repository modules.

---

## 2) Control Plane and Data Plane

### Control Plane
Responsible for policy, planning, scheduling, supervision, approvals, and safety:

- `core/orchestrator.py`
- `core/autonomy_engine.py`
- `core/scheduler.py`
- `governance/policy_engine.py`
- `governance/human_approval_service.py`
- `governance/guardrails.py`
- `scheduler/adaptive_scheduler.py`
- `scheduler/queue_backpressure_controller.py`

### Data Plane
Responsible for task execution, messaging, memory, and observability:

- `tasks/task_graph_engine.py`
- `tasks/task_decomposition_engine.py`
- `tasks/task_checkpoint_store.py`
- `agents/planner_agent.py`
- `agents/executor_agent.py`
- `agents/verifier_agent.py`
- `agents/supervisor_agent.py`
- `tools/tool_registry.py`
- `tools/sandbox_runner.py`
- `communication/event_bus.py`
- `communication/agent_mailbox.py`
- `memory/vector_memory.py`
- `memory/episodic_memory.py`
- `memory/knowledge_store.py`
- `monitoring/telemetry_service.py`
- `monitoring/anomaly_detector.py`
- `monitoring/alerts.py`

---

## 3) Module Responsibilities

### Core

- **`core/orchestrator.py`**
  - Entry point for each objective.
  - Executes policy check -> optional human approval -> graph creation -> schedule generation -> execution -> guardrail enforcement.
- **`core/autonomy_engine.py`**
  - Runs execution windows.
  - Emits runtime events and writes checkpoints for durability.
- **`core/scheduler.py`**
  - Scheduling kernel that combines adaptive ranking and backpressure controls.
- **`core/load_manager.py`**
  - Tracks distributed worker load and assigns work to least-loaded workers.

### Agents

- **`agents/planner_agent.py`**: Converts objectives into executable plans.
- **`agents/executor_agent.py`**: Performs tasks using registered tools.
- **`agents/verifier_agent.py`**: Validates correctness and policy compliance.
- **`agents/supervisor_agent.py`**: Oversees lower-level agents and escalates risks.

### Tasks

- **`tasks/task_graph_engine.py`**: Durable dependency DAG, state transitions, and readiness handling.
- **`tasks/task_decomposition_engine.py`**: Decomposes complex goals into bounded subtasks.
- **`tasks/task_checkpoint_store.py`**: Persistent execution checkpoints for replay/recovery.

### Memory

- **`memory/vector_memory.py`**: Semantic recall for decisions, results, and context.
- **`memory/episodic_memory.py`**: Ordered execution episodes for near-term continuity.
- **`memory/knowledge_store.py`**: Durable structured facts and operational knowledge.

### Tools

- **`tools/tool_registry.py`**: Central tool capability registry and policy-aware access control.
- **`tools/sandbox_runner.py`**: Sandboxed command execution with bounded timeouts.

### Communication

- **`communication/event_bus.py`**: Pub/sub eventing for decoupled control and observability.
- **`communication/agent_mailbox.py`**: Reliable per-agent async messaging.

### Governance

- **`governance/policy_engine.py`**: Preflight policy decisions and risk flags.
- **`governance/human_approval_service.py`**: Approval gates for risky actions.
- **`governance/guardrails.py`**: Runtime safety and cost controls.

### Monitoring

- **`monitoring/telemetry_service.py`**: Unified runtime telemetry events.
- **`monitoring/anomaly_detector.py`**: Detects cost/error spikes.
- **`monitoring/alerts.py`**: Emits alerts for policy, reliability, and budget incidents.

### Adaptive Scheduling

- **`scheduler/adaptive_scheduler.py`**: Priority/risk-aware dynamic scheduling.
- **`scheduler/queue_backpressure_controller.py`**: Limits dispatch during saturation.

---

## 4) End-to-End Execution Flow

1. Client submits objective to `Orchestrator`.
2. `PolicyEngine` evaluates action legality/risk.
3. `HumanApprovalService` gates high-risk actions.
4. `TaskDecompositionEngine` builds subtasks.
5. `TaskGraphEngine` stores graph and dependency metadata.
6. `SchedulingKernel` calls adaptive scheduler + backpressure controller.
7. `LoadManager` selects worker targets.
8. `ExecutorAgent` performs tasks via `ToolRegistry` + `SandboxRunner`.
9. `VerifierAgent` validates outputs.
10. `AutonomyEngine` writes `TaskCheckpointStore` updates and publishes events.
11. `SupervisorAgent` aggregates child outcomes and escalates as needed.
12. `Guardrails` enforces budget and safety limits before finalization.
13. `TelemetryService` + `AnomalyDetector` + `Alerts` provide production visibility.

---

## 5) Production Readiness Guarantees

### Distributed Workers

- Worker load tracking and placement through `LoadManager`.
- Event-driven execution via `EventBus` and mailbox-based command routing.

### Durable Task Graphs

- Graph states are checkpointed in `TaskCheckpointStore`.
- Recovery can replay checkpoints to reconstruct execution state.

### Hierarchical Supervision

- Planner -> Executor -> Verifier -> Supervisor chain supports layered control.
- Supervisor escalates high-severity policy/runtime failures.

### Adaptive Scheduling

- Priority ranking by `AdaptiveScheduler`.
- Throughput throttling by `QueueBackpressureController`.

### Human-in-the-Loop Governance

- Risky actions are paused pending explicit approval.
- Auditability preserved via approval request records + telemetry events.

### Guardrails and Cost Controls

- Hard and per-request budget caps enforced by `Guardrails`.
- Alerting and anomaly detection for cost spikes and error bursts.

---

## 6) Suggested Deployment Topology

- **Orchestrator Service**: control-plane APIs, policy checks, scheduling, supervision.
- **Worker Pool**: scalable executor/verifier workers.
- **State Store**: task graph + checkpoint persistence.
- **Event Backbone**: pub/sub broker for events and async notifications.
- **Monitoring Stack**: telemetry ingestion, anomaly detection, alert routing.

This topology enables horizontal scale while preserving governance, reliability, and recoverability.
