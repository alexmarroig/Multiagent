"""Modelos Pydantic para contratos da API do AgentOS."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    financial = "financial"
    travel = "travel"
    meeting = "meeting"
    phone = "phone"
    excel = "excel"
    marketing = "marketing"
    supervisor = "supervisor"


class LLMProvider(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    ollama = "ollama"


class NodeConfig(BaseModel):
    id: str
    agent_type: AgentType
    label: str
    model: str = ""
    provider: LLMProvider = LLMProvider.anthropic
    system_prompt: str = ""
    tools: list[str] = Field(default_factory=list)


class EdgeConfig(BaseModel):
    id: str
    source: str
    target: str


class FlowConfig(BaseModel):
    session_id: str = ""
    nodes: list[NodeConfig] = Field(default_factory=list)
    edges: list[EdgeConfig] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)


class AgentEvent(BaseModel):
    session_id: str
    agent_id: str
    agent_name: str
    event_type: str
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExcelConfig(BaseModel):
    title: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    sheet_name: str = "Dados"
    include_charts: bool = True
    filename: str = "relatorio.xlsx"


class MeetingConfig(BaseModel):
    title: str
    description: str = ""
    start_datetime: str
    end_datetime: str
    attendees: list[str] = Field(default_factory=list)


class CallConfig(BaseModel):
    to_number: str
    script: str
    language: str = "pt-BR"


class TravelConfig(BaseModel):
    destination: str
    checkin: str
    checkout: str
    adults: int = 1
    budget_brl: float | None = None
    preferences: list[str] = Field(default_factory=list)
