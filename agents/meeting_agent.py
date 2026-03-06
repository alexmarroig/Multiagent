from agents.base_agent import AgentSpec

MEETING_AGENT = AgentSpec(
    role="Executive Assistant",
    goal="Agendar reuniões e enviar confirmações",
    backstory="Assistente executivo com foco em eficiência operacional",
    default_tools=["calendar"],
)
