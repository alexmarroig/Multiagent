"""Ferramentas de navegador com Playwright."""

from __future__ import annotations

import asyncio
import json
import random
import threading
import time
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from playwright.async_api import async_playwright

_API_RATE_LOCK = threading.Lock()
_LAST_API_CALL_AT = 0.0
_MIN_CALL_INTERVAL_SECONDS = 1.25


def _throttled_get_json(url: str, timeout: int = 20, max_attempts: int = 4) -> dict | list:
    """Executa GET com rate limit local + retry/backoff simples."""
    global _LAST_API_CALL_AT

    user_agents = [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]

    for attempt in range(max_attempts):
        with _API_RATE_LOCK:
            now = time.monotonic()
            wait_for = _MIN_CALL_INTERVAL_SECONDS - (now - _LAST_API_CALL_AT)
            if wait_for > 0:
                time.sleep(wait_for)
            _LAST_API_CALL_AT = time.monotonic()

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": random.choice(user_agents),
            },
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except Exception:
            if attempt == max_attempts - 1:
                raise
            base = 0.7 * (2**attempt)
            time.sleep(base + random.uniform(0.1, 0.6))

    raise RuntimeError("Falha inesperada ao consultar API externa.")


def _geocode_destination(destination: str) -> tuple[float, float] | None:
    query = quote_plus(destination)
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=jsonv2&limit=1"
    result = _throttled_get_json(url)
    if isinstance(result, list) and result:
        return float(result[0]["lat"]), float(result[0]["lon"])
    return None


def _search_hotels_overpass(lat: float, lon: float, limit: int = 8) -> list[dict[str, str | float | None]]:
    # raio de ~8km; prioriza hotéis e apart-hotéis.
    query = quote_plus(
        f"""
        [out:json][timeout:25];
        (
          node[\"tourism\"~\"hotel|apartment|guest_house|hostel\"](around:8000,{lat},{lon});
          way[\"tourism\"~\"hotel|apartment|guest_house|hostel\"](around:8000,{lat},{lon});
        );
        out center {limit};
        """
    )
    url = f"https://overpass-api.de/api/interpreter?data={query}"
    result = _throttled_get_json(url, timeout=35)

    hotels = []
    for element in result.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        hotels.append(
            {
                "name": name,
                "category": tags.get("tourism"),
                "stars": tags.get("stars"),
                "phone": tags.get("phone"),
                "website": tags.get("website"),
                "price_brl": None,
            }
        )
    return hotels


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
    """Busca hotéis via APIs abertas (Nominatim + Overpass), com telemetria."""
    provider = "nominatim+overpass"
    try:
        coordinates = _geocode_destination(destination)
        if not coordinates:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Destino '{destination}' não encontrado.",
                    "destination": destination,
                    "checkin": checkin,
                    "checkout": checkout,
                    "guests": guests,
                    "provider": provider,
                    "mode": "real",
                },
                ensure_ascii=False,
            )

        lat, lon = coordinates
        options = _search_hotels_overpass(lat, lon)
        return json.dumps(
            {
                "success": True,
                "destination": destination,
                "checkin": checkin,
                "checkout": checkout,
                "guests": guests,
                "coordinates": {"lat": lat, "lon": lon},
                "options": options,
                "provider": provider,
                "mode": "real",
            },
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps(
            {
                "success": False,
                "error": str(exc),
                "destination": destination,
                "checkin": checkin,
                "checkout": checkout,
                "guests": guests,
                "provider": provider,
                "mode": "real",
            },
            ensure_ascii=False,
        )
