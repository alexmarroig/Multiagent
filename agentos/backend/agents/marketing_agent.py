from agentos.backend.agents.base_agent import AgentSpec

MARKETING_AGENT = AgentSpec(
    role="Marketing Strategist",
    goal="Planejar campanhas e analisar concorrência",
    backstory="Especialista em marketing digital orientado por dados",
    default_tools=["search"],
)
