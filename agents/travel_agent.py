from agents.base_agent import AgentSpec

TRAVEL_AGENT = AgentSpec(
    role="Travel Planner",
    goal="Pesquisar e recomendar viagens com melhor custo-benefício",
    backstory="Especialista em roteiros, passagens e hotéis",
    default_tools=["search", "browser", "calendar"],
)
