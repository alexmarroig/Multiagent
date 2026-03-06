"""Ferramentas de busca web."""

from __future__ import annotations

import os

from tavily import TavilyClient

from monitoring.tracing import get_tracer


def web_search(query: str) -> str:
    """Busca avançada na web e retorna resposta com top resultados."""
    tracer = get_tracer()
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "TAVILY_API_KEY não configurada."

    try:
        with tracer.start_span("external.web_search", kind="external_api_call", attributes={"provider": "tavily"}):
            client = TavilyClient(api_key=api_key)
            result = client.search(query=query, search_depth="advanced", include_answer=True, max_results=5)
        answer = result.get("answer", "Sem resposta direta.")
        lines = [f"Resposta: {answer}", "Resultados:"]
        for idx, item in enumerate(result.get("results", [])[:5], start=1):
            lines.append(f"{idx}. {item.get('title')} - {item.get('url')}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Erro na busca: {exc}"
