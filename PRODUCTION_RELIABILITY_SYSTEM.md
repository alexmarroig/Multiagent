# Production Reliability System

This repository now includes a production reliability framework for the autonomous agent platform.

## 1) Audit framework (`system_audit/`)

The framework provides modular runtime audits, each exposing:

- `run_audit() -> {name, status, details}`
- Status values: `OK`, `PARTIAL`, `FAILED`

Audits implemented:

- Task explosion protection
- Queue backpressure enforcement
- LLM budget enforcement
- Context management controls
- Circuit breaker protection
- Worker watchdog recovery
- Checkpoint persistence/recovery

`system_audit/audit_runner.py` executes all modules and prints a JSON report with `overall_status` and all audit results. It exits with status code `1` if any audit returns `FAILED`.

## 2) API reliability tests (`tests/api/`)

Pytest API tests cover:

- health endpoint
- task execution endpoint
- agent creation endpoint
- memory retrieval endpoint
- tool invocation endpoint

Coverage includes:

- response status code checks
- response schema checks
- timeout assertions
- error-handling assertions
- concurrent load simulation with thread pool requests

## 3) Reliability simulations (`tests/reliability/`)

Reliability tests simulate:

- task explosion attempts
- queue saturation
- LLM budget overrun
- worker crash recovery

Assertions verify throttling and responsiveness behavior.

## 4) Runtime health monitoring (`monitoring/system_health.py`)

A dedicated health service tracks:

- active agents
- queue depth
- worker utilization
- task success rate
- error rate
- LLM token consumption
- memory usage

Exposed endpoint:

- `GET /system/health`

## 5) Health dashboard (`dashboard/app.py`)

FastAPI dashboard provides:

- agent activity and utilization
- queue pressure
- worker health metrics
- error rates
- LLM usage indicators
- placeholder for recent alerts

The frontend refreshes health metrics every 5 seconds.

## 6) Alerting system (`monitoring/alerts.py`)

Alerts trigger on:

- high queue watermark breaches
- elevated error rates
- repeated worker crashes
- LLM budget overrun

Alert actions:

- structured log warning
- webhook dispatch stub
- email notification stub

## 7) CI/CD integration (`.github/workflows/system_checks.yml`)

GitHub Actions pipeline runs:

1. unit/integration tests
2. API tests
3. reliability tests
4. system audits

Build fails if `audit_runner` returns non-zero.

## 8) Observability hooks

Structured observability hooks were added using JSON logs with fields:

- `timestamp`
- `component`
- `event`
- `severity`

Core queue and watchdog components emit structured events for pressure transitions and worker recovery.

## 9) Stress test entrypoint (`stress_test.py`)

`stress_test.py` simulates high concurrency and queue pressure with hundreds of tasks. It outputs a report with:

- latency percentiles
- failure rate
- queue depth

## Production-grade classification

With audits, runtime monitoring, reliability simulations, CI/CD gating, alerting, stress testing, and observability in place, this platform now meets the baseline requirements for a **Production-grade Autonomous Agent Platform**.
