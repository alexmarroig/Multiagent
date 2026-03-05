"""Emergency controls for terminating unstable agents."""

from __future__ import annotations

from collections import defaultdict


class AgentKillSwitch:
    """Supports per-agent, per-tenant, and global emergency shutdowns."""

    def __init__(self) -> None:
        self._terminated_agents: set[str] = set()
        self._tenant_agents: dict[str, set[str]] = defaultdict(set)
        self._global_stop = False

    def register_agent(self, agent_id: str, tenant_id: str) -> None:
        self._tenant_agents[tenant_id].add(agent_id)

    def terminate_agent(self, agent_id: str) -> None:
        self._terminated_agents.add(agent_id)

    def terminate_tenant_agents(self, tenant_id: str) -> int:
        agents = self._tenant_agents.get(tenant_id, set())
        self._terminated_agents.update(agents)
        return len(agents)

    def emergency_stop(self) -> None:
        self._global_stop = True

    def is_terminated(self, agent_id: str) -> bool:
        return self._global_stop or agent_id in self._terminated_agents

    def is_global_stop_active(self) -> bool:
        return self._global_stop
