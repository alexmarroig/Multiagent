from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import AgentType


def test_templates_only_use_supported_agents() -> None:
    client = TestClient(app)
    response = client.get('/api/agents/templates')
    assert response.status_code == 200
    templates = response.json()

    allowed = {agent.value for agent in AgentType}
    for template in templates:
        for agent in template.get('agents', []):
            assert agent in allowed
