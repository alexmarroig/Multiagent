"""Estruturas base para definição de agentes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentSpec:
    """Configuração padrão de um agente para o builder."""

    role: str
    goal: str
    backstory: str
    default_tools: list[str] = field(default_factory=list)
