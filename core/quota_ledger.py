"""Durable quota and cost ledger for token-governed model usage."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


class QuotaExceededError(RuntimeError):
    """Raised when a debit would violate tenant/agent quota ceilings."""


@dataclass(slots=True, frozen=True)
class QuotaPolicy:
    tenant_token_quota: int
    agent_token_quota: int
    daily_cost_ceiling: float
    monthly_cost_ceiling: float


@dataclass(slots=True, frozen=True)
class QuotaDebit:
    tenant_id: str
    agent_id: str
    request_id: str
    tokens: int
    cost: float
    timestamp: float = field(default_factory=time.time)


class QuotaStore(Protocol):
    def read_usage(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> dict[str, float]: ...

    def atomic_debit(
        self,
        tenant_id: str,
        agent_id: str,
        day_key: str,
        month_key: str,
        tokens: int,
        cost: float,
        request_id: str,
    ) -> dict[str, float]: ...


class InMemoryQuotaStore:
    """Fallback store for tests/dev; production should use RedisQuotaStore/PostgresQuotaStore."""

    def __init__(self) -> None:
        self._state: dict[str, float] = {}
        self._lock = threading.RLock()

    def _k(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> list[str]:
        return [
            f"tenant:{tenant_id}:tokens",
            f"agent:{tenant_id}:{agent_id}:tokens",
            f"tenant:{tenant_id}:cost:day:{day_key}",
            f"tenant:{tenant_id}:cost:month:{month_key}",
        ]

    def read_usage(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> dict[str, float]:
        keys = self._k(tenant_id, agent_id, day_key, month_key)
        with self._lock:
            return {
                "tenant_tokens": float(self._state.get(keys[0], 0.0)),
                "agent_tokens": float(self._state.get(keys[1], 0.0)),
                "daily_cost": float(self._state.get(keys[2], 0.0)),
                "monthly_cost": float(self._state.get(keys[3], 0.0)),
            }

    def atomic_debit(self, tenant_id: str, agent_id: str, day_key: str, month_key: str, tokens: int, cost: float, request_id: str) -> dict[str, float]:
        keys = self._k(tenant_id, agent_id, day_key, month_key)
        with self._lock:
            if self._state.get(f"audit:{request_id}") is not None:
                return self.read_usage(tenant_id, agent_id, day_key, month_key)
            self._state[keys[0]] = self._state.get(keys[0], 0.0) + tokens
            self._state[keys[1]] = self._state.get(keys[1], 0.0) + tokens
            self._state[keys[2]] = self._state.get(keys[2], 0.0) + cost
            self._state[keys[3]] = self._state.get(keys[3], 0.0) + cost
            self._state[f"audit:{request_id}"] = time.time()
        return self.read_usage(tenant_id, agent_id, day_key, month_key)


class RedisQuotaStore:
    """Redis-backed durable and atomic quota updates via WATCH/MULTI/EXEC."""

    def __init__(self, redis_client: Any) -> None:
        self.redis = redis_client

    def _k(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> list[str]:
        return [
            f"quota:tenant:{tenant_id}:tokens",
            f"quota:agent:{tenant_id}:{agent_id}:tokens",
            f"quota:tenant:{tenant_id}:cost:day:{day_key}",
            f"quota:tenant:{tenant_id}:cost:month:{month_key}",
        ]

    def read_usage(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> dict[str, float]:
        keys = self._k(tenant_id, agent_id, day_key, month_key)
        values = self.redis.mget(keys)
        return {
            "tenant_tokens": float(values[0] or 0),
            "agent_tokens": float(values[1] or 0),
            "daily_cost": float(values[2] or 0),
            "monthly_cost": float(values[3] or 0),
        }

    def atomic_debit(self, tenant_id: str, agent_id: str, day_key: str, month_key: str, tokens: int, cost: float, request_id: str) -> dict[str, float]:
        keys = self._k(tenant_id, agent_id, day_key, month_key)
        audit_key = f"quota:audit:{request_id}"
        with self.redis.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(*keys, audit_key)
                    if pipe.get(audit_key):
                        pipe.unwatch()
                        return self.read_usage(tenant_id, agent_id, day_key, month_key)
                    pipe.multi()
                    pipe.incrbyfloat(keys[0], float(tokens))
                    pipe.incrbyfloat(keys[1], float(tokens))
                    pipe.incrbyfloat(keys[2], float(cost))
                    pipe.incrbyfloat(keys[3], float(cost))
                    pipe.set(audit_key, json.dumps({"tenant_id": tenant_id, "agent_id": agent_id, "tokens": tokens, "cost": cost, "ts": time.time()}), ex=60 * 60 * 24 * 90)
                    pipe.execute()
                    break
                except Exception:
                    continue
        return self.read_usage(tenant_id, agent_id, day_key, month_key)


class PostgresQuotaStore:
    """Postgres-backed quota store with serializable tx updates."""

    def __init__(self, conn: Any) -> None:
        self.conn = conn

    def _ensure_schema(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS quota_usage (
                    scope TEXT NOT NULL,
                    key TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    PRIMARY KEY (scope, key)
                );
                CREATE TABLE IF NOT EXISTS quota_audit (
                    request_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL
                );
                """
            )
            self.conn.commit()

    def _get(self, scope: str, key: str) -> float:
        with self.conn.cursor() as cur:
            cur.execute("SELECT amount FROM quota_usage WHERE scope=%s AND key=%s", (scope, key))
            row = cur.fetchone()
            return float(row[0]) if row else 0.0

    def _upsert_increment(self, scope: str, key: str, amount: float) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO quota_usage(scope, key, amount) VALUES(%s, %s, %s)
                ON CONFLICT(scope, key) DO UPDATE SET amount = quota_usage.amount + EXCLUDED.amount
                """,
                (scope, key, amount),
            )

    def read_usage(self, tenant_id: str, agent_id: str, day_key: str, month_key: str) -> dict[str, float]:
        self._ensure_schema()
        return {
            "tenant_tokens": self._get("tenant_tokens", tenant_id),
            "agent_tokens": self._get("agent_tokens", f"{tenant_id}:{agent_id}"),
            "daily_cost": self._get("daily_cost", f"{tenant_id}:{day_key}"),
            "monthly_cost": self._get("monthly_cost", f"{tenant_id}:{month_key}"),
        }

    def atomic_debit(self, tenant_id: str, agent_id: str, day_key: str, month_key: str, tokens: int, cost: float, request_id: str) -> dict[str, float]:
        self._ensure_schema()
        self.conn.autocommit = False
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT request_id FROM quota_audit WHERE request_id=%s", (request_id,))
                if cur.fetchone() is not None:
                    return self.read_usage(tenant_id, agent_id, day_key, month_key)
            self._upsert_increment("tenant_tokens", tenant_id, float(tokens))
            self._upsert_increment("agent_tokens", f"{tenant_id}:{agent_id}", float(tokens))
            self._upsert_increment("daily_cost", f"{tenant_id}:{day_key}", float(cost))
            self._upsert_increment("monthly_cost", f"{tenant_id}:{month_key}", float(cost))
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO quota_audit(request_id, tenant_id, agent_id, created_at) VALUES(%s, %s, %s, %s)",
                    (request_id, tenant_id, agent_id, time.time()),
                )
        return self.read_usage(tenant_id, agent_id, day_key, month_key)


class DurableQuotaLedger:
    def __init__(self, store: QuotaStore, *, policies: dict[str, QuotaPolicy] | None = None, default_policy: QuotaPolicy | None = None) -> None:
        self.store = store
        self.policies = policies or {}
        self.default_policy = default_policy or QuotaPolicy(tenant_token_quota=1_000_000, agent_token_quota=250_000, daily_cost_ceiling=1000.0, monthly_cost_ceiling=20_000.0)
        self._lock = threading.Lock()

    def _time_keys(self, now: float | None = None) -> tuple[str, str]:
        dt = datetime.fromtimestamp(now or time.time(), tz=UTC)
        return dt.strftime("%Y-%m-%d"), dt.strftime("%Y-%m")

    def policy_for(self, tenant_id: str) -> QuotaPolicy:
        return self.policies.get(tenant_id, self.default_policy)

    def debit(self, debit: QuotaDebit) -> dict[str, float]:
        day_key, month_key = self._time_keys(debit.timestamp)
        policy = self.policy_for(debit.tenant_id)
        with self._lock:
            current = self.store.read_usage(debit.tenant_id, debit.agent_id, day_key, month_key)
            if current["tenant_tokens"] + debit.tokens > policy.tenant_token_quota:
                raise QuotaExceededError("tenant token quota exceeded")
            if current["agent_tokens"] + debit.tokens > policy.agent_token_quota:
                raise QuotaExceededError("agent token quota exceeded")
            if current["daily_cost"] + debit.cost > policy.daily_cost_ceiling:
                raise QuotaExceededError("daily cost ceiling exceeded")
            if current["monthly_cost"] + debit.cost > policy.monthly_cost_ceiling:
                raise QuotaExceededError("monthly cost ceiling exceeded")
            return self.store.atomic_debit(
                debit.tenant_id,
                debit.agent_id,
                day_key,
                month_key,
                debit.tokens,
                debit.cost,
                debit.request_id,
            )
