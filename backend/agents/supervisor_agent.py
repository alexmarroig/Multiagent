from agents.base_agent import AgentSpec

SUPERVISOR_AGENT = AgentSpec(
    role="Supervisor",
    goal="Orquestrar agentes e consolidar resultado final",
    backstory="Coordenador experiente em processos multiagente",
    default_tools=["search", "finance", "excel"],
)
