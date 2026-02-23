"""Ferramentas de navegador com Playwright."""

from __future__ import annotations

import asyncio
import json

from playwright.async_api import async_playwright


async def _browse(url: str) -> dict[str, str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            title = await page.title()
            text = (await page.inner_text("body"))[:5000]
            return {"title": title, "content": text}
        finally:
            await browser.close()


def browse_website(url: str, task: str = "extrair conteúdo principal") -> str:
    """Navega em uma URL e retorna título e texto limitado."""
    try:
        result = asyncio.run(_browse(url))
        return json.dumps({"task": task, **result}, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "task": task}, ensure_ascii=False)


def search_hotels(destination: str, checkin: str, checkout: str, guests: int = 2) -> str:
    """Retorna opções simuladas de hotéis (MVP)."""
    options = [
        {"name": f"{destination} Central Hotel", "price_brl": 780, "rating": 8.9},
        {"name": f"{destination} Comfort Suites", "price_brl": 620, "rating": 8.5},
        {"name": f"{destination} Budget Inn", "price_brl": 430, "rating": 7.9},
    ]
    return json.dumps(
        {
            "destination": destination,
            "checkin": checkin,
            "checkout": checkout,
            "guests": guests,
            "options": options,
            "todo": "Implementar integração real via Playwright/Booking API",
        },
        ensure_ascii=False,
    )
