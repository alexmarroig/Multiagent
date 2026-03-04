from agentos.backend.security.rbac import Permission, RBACAuthorizationError, RBACContext, RBACResource, rbac_middleware


def test_operator_can_invoke_tools_in_same_tenant() -> None:
    context = RBACContext(user_id="u1", roles=("operator",), tenant_id="t1", scopes=("tenant",))
    resource = RBACResource(resource_type="tool", action="invoke", tenant_id="t1", scope="tenant")

    rbac_middleware.authorize(context=context, permission=Permission.TOOL_INVOKE, resource=resource)


def test_operator_cannot_cross_tenant_boundary() -> None:
    context = RBACContext(user_id="u1", roles=("operator",), tenant_id="t1", scopes=("tenant",))
    resource = RBACResource(resource_type="memory", action="read", tenant_id="t2", scope="tenant")

    try:
        rbac_middleware.authorize(context=context, permission=Permission.MEMORY_READ, resource=resource)
    except RBACAuthorizationError as exc:
        assert "Cross-tenant access denied" in str(exc)
    else:
        raise AssertionError("Expected cross-tenant request to be blocked")


def test_viewer_cannot_take_governance_decision() -> None:
    context = RBACContext(user_id="u2", roles=("viewer",), tenant_id="t1", scopes=("own",))
    resource = RBACResource(resource_type="governance", action="approve", tenant_id="t1", scope="tenant")

    try:
        rbac_middleware.authorize(context=context, permission=Permission.GOVERNANCE_DECIDE, resource=resource)
    except RBACAuthorizationError as exc:
        assert "Permission" in str(exc)
    else:
        raise AssertionError("Expected governance decision to be denied for viewer")
