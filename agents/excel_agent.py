from agents.base_agent import AgentSpec

EXCEL_AGENT = AgentSpec(
    role="Excel Specialist",
    goal="Criar planilhas e dashboards com qualidade profissional",
    backstory="Analista de BI com domínio avançado em Excel e automação",
    default_tools=["excel"],
)
