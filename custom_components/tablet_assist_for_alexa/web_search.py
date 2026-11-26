"""Optional local SearXNG search, installed only when explicitly configured.

The integration never searches the internet without a user query. A search
engine must be on a private LAN; result URLs are public HTTPS links only.
"""
import ipaddress
import re
from urllib.parse import urlsplit

import aiohttp
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

COMMAND = DOMAIN + "/search"
SEARCH_PATTERN = re.compile(
    r"^(?:(?:hey\s+)?(?:jarvis|tafa)[,\s]+)?(?:bitte\s+)?"
    r"(?:such(?:e)?|recherchier(?:e)?)\s+(?:(?:bitte|mal)\s+)*"
    r"(?:im\s+(?:internet|web)(?:\s+nach)?|online(?:\s+nach)?|nach)\s+(.{2,160})[.!?]?$", re.I)
FOLLOW_PATTERN = re.compile(r"^(?:oeffne|öffne|zeig(?:e)?)\s+(?:treffer\s+)?(?:nummer\s+)?([1-9]|zehn|eins|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun)\b", re.I)
NUMBERS = {"eins": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "fuenf": 5,
           "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10}


def validate_local_search_origin(raw):
    """Refuse arbitrary URLs, credentials, public destinations, and DNS names."""
    if raw == "":
        return ""
    if not isinstance(raw, str) or len(raw) > 180:
        raise ValueError("Invalid SearXNG address")
    url = urlsplit(raw.strip().rstrip("/"))
    if url.scheme != "http" or not url.hostname or not url.port or url.path or url.query or url.fragment or url.username or url.password:
        raise ValueError("SearXNG must be a local HTTP host:port without credentials or path")
    try:
        ip = ipaddress.ip_address(url.hostname)
        allowed = ip.version == 4 and ip.is_private and not ip.is_loopback and not ip.is_link_local
    except ValueError:
        allowed = url.hostname.endswith(".local") and re.fullmatch(r"[A-Za-z0-9.-]+", url.hostname)
    if not allowed:
        raise ValueError("SearXNG must be on a private LAN")
    return raw.strip().rstrip("/")


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
        async with session.get(base + "/search", params={"q": query, "format": "json", "language": "de"},
                               timeout=aiohttp.ClientTimeout(total=12), allow_redirects=False) as response:
            if response.status != 200 or response.content_length and response.content_length > 180000:
                raise ValueError("SearXNG JSON API unavailable")
            content = await response.content.read(180001)
            if len(content) > 180000:
                raise ValueError("Search result too large")
            import json
            payload = json.loads(content)
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
