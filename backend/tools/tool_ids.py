"""Fonte única de verdade para IDs de ferramentas no backend."""

from __future__ import annotations

from typing import Final

CANONICAL_TOOL_IDS: Final[tuple[str, ...]] = (
    "finance",
    "excel",
    "phone",
    "calendar",
    "search",
    "browser",
    "travel",
)

TOOL_ID_ALIASES: Final[dict[str, str]] = {
    "yfinance": "finance",
    "openpyxl": "excel",
    "pandas": "excel",
    "twilio": "phone",
    "google-calendar": "calendar",
    "tavily": "search",
    "playwright": "browser",
}


def normalize_tool_id(tool_id: str) -> str | None:
    normalized = tool_id.strip().lower()
    if not normalized:
        return None
    if normalized in CANONICAL_TOOL_IDS:
        return normalized
    return TOOL_ID_ALIASES.get(normalized)


def normalize_tool_ids(tool_ids: list[str]) -> tuple[list[str], list[str]]:
    normalized: list[str] = []
    unmapped: list[str] = []

    for tool_id in tool_ids:
        mapped = normalize_tool_id(tool_id)
        if mapped:
            if mapped not in normalized:
                normalized.append(mapped)
        else:
            unmapped.append(tool_id)

    return normalized, unmapped
