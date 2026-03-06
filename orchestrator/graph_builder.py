"""Builder LangGraph para fluxos avançados (base MVP)."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from models.schemas import FlowConfig


class GraphState(TypedDict):
    payload: dict


def build_langgraph(flow: FlowConfig):
    """Cria um grafo mínimo para futura evolução com estados complexos."""

    def passthrough(state: GraphState) -> GraphState:
        return state

    graph = StateGraph(GraphState)
    graph.add_node("start", passthrough)
    graph.set_entry_point("start")
    graph.add_edge("start", END)
    return graph.compile()
