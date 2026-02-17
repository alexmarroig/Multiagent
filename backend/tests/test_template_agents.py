from __future__ import annotations

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.routes_agents import list_templates
from models.schemas import AgentType


def test_templates_only_use_supported_agent_types() -> None:
    templates = asyncio.run(list_templates())
    supported = {agent.value for agent in AgentType}

    invalid_by_template: dict[str, list[str]] = {}

    for template in templates:
        invalid_agents = [agent for agent in template["agents"] if agent not in supported]
        if invalid_agents:
            invalid_by_template[template["id"]] = invalid_agents

    assert invalid_by_template == {}, f"Templates com agentes inválidos: {invalid_by_template}"


def test_templates_have_at_least_one_agent() -> None:
    templates = asyncio.run(list_templates())

    empty_templates = [template["id"] for template in templates if not template["agents"]]
    assert empty_templates == [], f"Templates sem agentes: {empty_templates}"
