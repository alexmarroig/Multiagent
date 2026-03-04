"""Role-based authorization middleware with tenant isolation and resource scopes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class Permission(StrEnum):
    AGENT_CREATE = "agent.create"
    TOOL_INVOKE = "tool.invoke"
    MEMORY_READ = "memory.read"
    MEMORY_WRITE = "memory.write"
    GOVERNANCE_READ = "governance.read"
    GOVERNANCE_DECIDE = "governance.decide"


class RBACAuthorizationError(PermissionError):
    """Raised when an authorization check fails."""


@dataclass(frozen=True)
class RBACResource:
    resource_type: str
    action: str
    resource_id: str | None = None
    tenant_id: str | None = None
    scope: str = "tenant"


@dataclass(frozen=True)
class RBACContext:
    user_id: str
    roles: tuple[str, ...]
    tenant_id: str | None = None
    scopes: tuple[str, ...] = ("tenant",)


@dataclass(frozen=True)
class RolePolicy:
    permissions: frozenset[Permission]
    scopes: frozenset[str] = field(default_factory=lambda: frozenset({"tenant"}))


DEFAULT_ROLE_POLICIES: dict[str, RolePolicy] = {
    "super_admin": RolePolicy(permissions=frozenset(Permission), scopes=frozenset({"tenant", "global", "own"})),
    "admin": RolePolicy(
        permissions=frozenset(
            {
                Permission.AGENT_CREATE,
                Permission.TOOL_INVOKE,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.GOVERNANCE_READ,
                Permission.GOVERNANCE_DECIDE,
            }
        ),
        scopes=frozenset({"tenant", "own"}),
    ),
    "operator": RolePolicy(
        permissions=frozenset(
            {
                Permission.AGENT_CREATE,
                Permission.TOOL_INVOKE,
                Permission.MEMORY_READ,
                Permission.MEMORY_WRITE,
                Permission.GOVERNANCE_READ,
            }
        ),
        scopes=frozenset({"tenant", "own"}),
    ),
    "auditor": RolePolicy(
        permissions=frozenset({Permission.GOVERNANCE_READ, Permission.MEMORY_READ}),
        scopes=frozenset({"tenant", "own"}),
    ),
    "viewer": RolePolicy(
        permissions=frozenset({Permission.MEMORY_READ}),
        scopes=frozenset({"own"}),
    ),
    "system": RolePolicy(permissions=frozenset(Permission), scopes=frozenset({"tenant", "global", "own"})),
}


class RBACMiddleware:
    """Central authorization gate for API and service-level access checks."""

    def __init__(self, role_policies: dict[str, RolePolicy] | None = None) -> None:
        self._role_policies = role_policies or DEFAULT_ROLE_POLICIES

    def context_from_user(self, user: dict, *, fallback_roles: Iterable[str] = ("viewer",)) -> RBACContext:
        role_value = user.get("role")
        roles = tuple(role_value) if isinstance(role_value, list) else ((role_value,) if role_value else tuple(fallback_roles))
        tenant_id = user.get("tenant_id") or user.get("organization_id")
        scopes = tuple(user.get("rbac_scopes") or ["tenant"])
        return RBACContext(user_id=str(user.get("id", "unknown")), roles=roles, tenant_id=tenant_id, scopes=scopes)

    def authorize(self, *, context: RBACContext, permission: Permission, resource: RBACResource) -> None:
        policies = [self._role_policies.get(role) for role in context.roles]
        effective = [policy for policy in policies if policy is not None]
        if not effective:
            raise RBACAuthorizationError("No RBAC policy is attached to the caller role")

        allowed_permissions = {perm for policy in effective for perm in policy.permissions}
        if permission not in allowed_permissions:
            raise RBACAuthorizationError(f"Permission '{permission}' is required for this operation")

        allowed_scopes = {scope for policy in effective for scope in policy.scopes}
        if resource.scope not in allowed_scopes:
            raise RBACAuthorizationError(
                f"Resource scope '{resource.scope}' is not accessible with caller scope {sorted(allowed_scopes)}"
            )

        self._enforce_tenant_isolation(context=context, resource=resource)

    @staticmethod
    def _enforce_tenant_isolation(*, context: RBACContext, resource: RBACResource) -> None:
        if resource.tenant_id is None:
            return
        if "super_admin" in context.roles or "system" in context.roles:
            return
        if context.tenant_id is None:
            raise RBACAuthorizationError("Caller has no tenant context for tenant-scoped resource")
        if context.tenant_id != resource.tenant_id:
            raise RBACAuthorizationError("Cross-tenant access denied")


rbac_middleware = RBACMiddleware()
SYSTEM_CONTEXT = RBACContext(user_id="system", roles=("system",), tenant_id=None, scopes=("global", "tenant", "own"))
