"""Optional local SearXNG search, installed only when explicitly configured.

The integration never searches the internet without a user query. A search
engine must be on a private LAN; result URLs are public HTTPS links only.
"""
import asyncio
import json
import ipaddress
import re
from urllib.parse import urlsplit

import aiohttp
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .local_intents import SEARCH_PATTERN, FOLLOW_PATTERN, NUMBERS
from .sources import validate_local_search_origin

COMMAND = DOMAIN + "/search"
def public_link(url):
    try:
        value = urlsplit(str(url))
        if value.scheme != "https" or not value.hostname or value.username or value.password or value.port:
            return None
        host = value.hostname.lower()
        ip = None
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            pass
        if ip is not None or "." not in host or host.endswith((".local", ".internal", ".onion")):
            return None
        return str(url)[:1024]
    except (TypeError, ValueError):
        return None


async def query_searxng(hass, base, query):
    if not base:
        return {"message": "SearXNG ist noch nicht eingerichtet. Im TAFA Control Center kannst du den Suchserver später verbinden.", "results": []}
    query = str(query or "").strip()
    if not 2 <= len(query) <= 160:
        return {"message": "Bitte nenne einen kürzeren Suchbegriff.", "results": []}
    try:
        base = validate_local_search_origin(base)
        session = async_get_clientsession(hass)
        payload = None
        # Some SearXNG engines briefly return 429/503 while aggregating.
        # One bounded retry helps without repeatedly hammering the server.
        for attempt in range(2):
            try:
                async with session.get(base + "/search",
                                       params={"q": query, "format": "json", "language": "de", "safesearch": "2"},
                                       timeout=aiohttp.ClientTimeout(total=18), allow_redirects=False) as response:
                    if response.status in (429, 502, 503, 504) and attempt == 0:
                        await asyncio.sleep(0.4)
                        continue
                    if response.status != 200:
                        raise ValueError("SearXNG JSON API unavailable")
                    if response.content_length and response.content_length > 1048576:
                        raise ValueError("SearXNG response too large")
                    content = await response.content.read(1048577)
                    if len(content) > 1048576:
                        raise ValueError("SearXNG response too large")
                    payload = json.loads(content)
                break
            except (aiohttp.ClientError, TimeoutError):
                if attempt == 0:
                    await asyncio.sleep(0.4)
                    continue
                raise
        if not isinstance(payload, dict):
            raise ValueError("SearXNG did not return a JSON object")
        rows = []
        for item in payload.get("results", []):
            if not isinstance(item, dict):
                continue
            url = public_link(item.get("url"))
            title = str(item.get("title", "")).strip()[:160]
            if url and title:
                rows.append({"title": title, "url": url, "snippet": str(item.get("content", "")).strip()[:270]})
            if len(rows) >= 10:
                break
        msg = ("Ich habe " + str(len(rows)) + " Suchtreffer gefunden. Du kannst sie auf dem TAFA-Dashboard öffnen."
               if rows else "SearXNG hat keine passenden Treffer geliefert.")
        return {"message": msg, "results": rows}
    except (aiohttp.ClientError, TimeoutError, ValueError, TypeError, KeyError):
        return {"message": "Die lokale Internetsuche ist momentan nicht erreichbar. Prüfe SearXNG und die aktivierte JSON-Ausgabe.", "results": []}


@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("query"): vol.All(str, vol.Length(min=2, max=160)),
})
@websocket_api.async_response
async def search_command(hass, connection, msg):
    entries = hass.config_entries.async_entries(DOMAIN)
    cfg = {**entries[0].data, **entries[0].options} if len(entries) == 1 else {}
    result = await query_searxng(hass, cfg.get("search_base", ""), msg["query"])
    connection.send_result(msg["id"], result)
