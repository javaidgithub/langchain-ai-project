"""Web tools: search, Wikipedia, URL fetching, weather."""
import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool

UA = {"User-Agent": "langchain-ai-project/1.0 (+https://github.com)"}


def _ddgs_search(query: str, max_results: int) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:  # pragma: no cover
        from duckduckgo_search import DDGS  # type: ignore
    return list(DDGS().text(query, max_results=max_results))


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web (DuckDuckGo) for current information. Returns titles, URLs and snippets."""
    try:
        results = await asyncio.to_thread(_ddgs_search, query, max(1, min(max_results, 10)))
    except Exception as exc:
        return f"Web search failed: {exc}"
    if not results:
        return "No results found."
    return "\n\n".join(f"[{i}] {r.get('title')}\n{r.get('href')}\n{r.get('body')}" for i, r in enumerate(results, 1))


@tool
async def wikipedia(query: str) -> str:
    """Look up a topic on Wikipedia and return the introduction of the best matching article."""
    try:
        return await _wikipedia(query)
    except Exception as exc:
        return f"Wikipedia lookup failed: {exc}"


async def _wikipedia(query: str) -> str:
    async with httpx.AsyncClient(timeout=15, headers=UA) as client:
        search = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1},
        )
        hits = search.json().get("query", {}).get("search", [])
        if not hits:
            return f"No Wikipedia article found for '{query}'."
        title = hits[0]["title"]
        page = await client.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "prop": "extracts", "exintro": 1, "explaintext": 1,
                    "titles": title, "format": "json", "redirects": 1},
        )
        pages = page.json()["query"]["pages"]
        extract = next(iter(pages.values())).get("extract", "")
    return f"{title}\nhttps://en.wikipedia.org/wiki/{title.replace(' ', '_')}\n\n{extract[:4000]}"


def _is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


@tool
async def fetch_url(url: str) -> str:
    """Download a web page and return its readable text (first ~6000 characters). Public http(s) URLs only."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return "Only http(s) URLs are supported."
    if not await asyncio.to_thread(_is_public_host, parsed.hostname):
        return "Refused: URL resolves to a private or local address."
    try:
        async with httpx.AsyncClient(timeout=20, headers=UA, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception as exc:
        return f"Fetch failed: {exc}"
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:6000] or "The page has no readable text."


@tool
async def get_weather(city: str) -> str:
    """Get the current weather for a city (uses the free Open-Meteo API, no key needed)."""
    try:
        return await _weather(city)
    except Exception as exc:
        return f"Weather lookup failed: {exc}"


async def _weather(city: str) -> str:
    async with httpx.AsyncClient(timeout=15, headers=UA) as client:
        geo = await client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1})
        results = geo.json().get("results")
        if not results:
            return f"Could not find a location called '{city}'."
        place = results[0]
        wx = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": place["latitude"], "longitude": place["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"},
        )
        cur = wx.json()["current"]
    return (f"{place['name']}, {place.get('country', '')}: {cur['temperature_2m']}°C, "
            f"humidity {cur['relative_humidity_2m']}%, wind {cur['wind_speed_10m']} km/h, "
            f"precipitation {cur['precipitation']} mm")
