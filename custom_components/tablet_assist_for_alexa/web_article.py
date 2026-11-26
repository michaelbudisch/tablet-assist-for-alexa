"""Read a public HTTPS result as bounded plain text or schema.org Recipe data.

This is a read-only optional extension. It never uses a browser iframe, sends
HA credentials to the source, follows redirects, or contacts private IPs.
"""
from __future__ import annotations

import asyncio
import html
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
from urllib.parse import urlsplit

import aiohttp
from aiohttp.resolver import DefaultResolver
import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN
from .web_search import public_link

COMMAND = DOMAIN + "/article_read"
MAX_HTML = 650_000
MAX_VISIBLE = 10_000


class PublicResolver:
    """Use only globally routable DNS answers, including on reconnects."""
    def __init__(self):
        self._resolver = DefaultResolver()

    async def resolve(self, host, port=0, family=socket.AF_INET):
        answers = await self._resolver.resolve(host, port, family=family)
        if not answers or any(not ipaddress.ip_address(row["host"]).is_global
                              for row in answers):
            raise ValueError("Article host is not a public address")
        return answers

    async def close(self):
        await self._resolver.close()


def clean(value, limit=600):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]{0,300}>", " ", value))).strip()[:limit]


def find_recipe(value, depth=0):
    """Find a source-provided JSON-LD Recipe; do not infer missing ingredients."""
    if depth > 6:
        return None
    if isinstance(value, list):
        for item in value[:40]:
            found = find_recipe(item, depth + 1)
            if found:
                return found
    if isinstance(value, dict):
        types = value.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if isinstance(types, list) and "Recipe" in types:
            return value
        for key in ("@graph", "mainEntity", "itemListElement", "about"):
            found = find_recipe(value.get(key), depth + 1)
            if found:
                return found
    return None


def steps_from(value, level=0):
    if level > 5:
        return []
    if isinstance(value, str):
        return [clean(value, 650)] if clean(value, 650) else []
    if isinstance(value, list):
        out = []
        for item in value[:35]:
            out.extend(steps_from(item, level + 1))
            if len(out) >= 18:
                break
        return out[:18]
    if isinstance(value, dict):
        if isinstance(value.get("itemListElement"), list):
            return steps_from(value["itemListElement"], level + 1)
        return steps_from(value.get("text", ""), level + 1)
    return []


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocked = 0
        self._ld = False
        self._ld_parts = []
        self.jsonld = []
        self._visible = []
        self._current = None
        self.title = ""
        self._title_parts = []
        self._in_title = False
        self._parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.blocked += 1
            self._ld = "ld+json" in str(attrs.get("type", "")).lower()
            self._ld_parts = []
            return
        if tag in ("style", "nav", "footer", "header", "svg", "noscript", "template"):
            self.blocked += 1
            return
        if self.blocked:
            return
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        if tag in ("p", "li", "h1", "h2", "h3") and self._current is None:
            self._current = tag
            self._parts = []

    def handle_data(self, data):
        if self._ld:
            if sum(map(len, self._ld_parts)) < 90_000:
                self._ld_parts.append(data)
        elif not self.blocked:
            if self._in_title:
                self._title_parts.append(data)
            if self._current is not None and len(self._parts) < 200:
                self._parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.blocked:
            if self._ld:
                try:
                    self.jsonld.append(json.loads("".join(self._ld_parts)))
                except (ValueError, TypeError):
                    pass
            self.blocked -= 1
            self._ld = False
            self._ld_parts = []
            return
        if tag in ("style", "nav", "footer", "header", "svg", "noscript", "template") and self.blocked:
            self.blocked -= 1
            return
        if self.blocked:
            return
        if tag == "title":
            self._in_title = False
            self.title = clean(" ".join(self._title_parts), 180)
        if self._current == tag:
            text = clean(" ".join(self._parts), 600)
            if text and len(self._visible) < 120:
                self._visible.append(text)
            self._parts = []
            self._current = None

    def result(self, url):
        recipe_data = None
        for node in self.jsonld[:25]:
            recipe_data = find_recipe(node)
            if recipe_data:
                break
        recipe = None
        if recipe_data:
            ingredients = recipe_data.get("recipeIngredient", [])
            if not isinstance(ingredients, list):
                ingredients = []
            quantity = recipe_data.get("recipeYield", "")
            if isinstance(quantity, list):
                quantity = ", ".join(clean(x, 50) for x in quantity[:4])
            recipe = {
                "name": clean(recipe_data.get("name", "") or self.title, 140),
                "ingredients": [clean(i, 220) for i in ingredients[:35] if clean(i, 220)],
                "steps": steps_from(recipe_data.get("recipeInstructions")),
                "yield": clean(quantity, 80),
            }
            if not recipe["ingredients"] and not recipe["steps"]:
                recipe = None
        paragraphs = []
        seen = set()
        for item in self._visible:
            if item in seen or len(item) < 20:
                continue
            seen.add(item)
            paragraphs.append(item)
        text = "\n\n".join(paragraphs)[:MAX_VISIBLE]
        title = (recipe.get("name") if recipe else None) or self.title or urlsplit(url).hostname
        if not text and not recipe:
            raise ValueError("No readable article content")
        summary = (recipe["name"] + ": " + str(len(recipe["ingredients"])) +
                   " Zutaten, " + str(len(recipe["steps"])) + " Zubereitungsschritte. "
                   + (recipe["steps"][0][:145] if recipe["steps"] else "")) if recipe else (
                   text[:380].rsplit(" ", 1)[0].strip() if len(text) > 380 else text)
        return {
            "title": title, "url": url, "text": text,
            "summary": summary, "summary_source": "excerpt",
            "voice_summary": summary[:370],
            "recipe": recipe, "word_count": len(text.split()),
        }


async def read_public_article(url):
    link = public_link(url)
    if not link or not re.fullmatch(r"[A-Za-z0-9.-]{3,253}", urlsplit(link).hostname or ""):
        raise ValueError("Only public HTTPS article URLs are supported")
    timeout = aiohttp.ClientTimeout(total=16, connect=5, sock_read=8)
    connector = aiohttp.TCPConnector(resolver=PublicResolver(), use_dns_cache=False,
                                    limit=2, ttl_dns_cache=0)
    async with aiohttp.ClientSession(connector=connector, trust_env=False,
                                     timeout=timeout) as session:
        # Follow at most two redirects. Every hop must stay public HTTPS and is
        # DNS-validated by the connector before any connection is established.
        for hop in range(3):
            async with session.get(link, allow_redirects=False,
                                   headers={"Accept": "text/html,application/xhtml+xml",
                                            "User-Agent": "TAFA-ArticleReader/1.0"}) as response:
                if response.status in (301, 302, 303, 307, 308):
                    from urllib.parse import urljoin
                    candidate = urljoin(link, response.headers.get("Location", ""))
                    if hop >= 2 or not public_link(candidate):
                        raise ValueError("The article redirect was not allowed")
                    link = candidate
                    continue
                if response.status != 200:
                    raise ValueError("Article HTTP status " + str(response.status))
                media = response.headers.get("Content-Type", "").lower()
                if "text/html" not in media and "application/xhtml+xml" not in media:
                    raise ValueError("The source is not an HTML article")
                if response.content_length and response.content_length > MAX_HTML:
                    raise ValueError("Article is too large")
                raw = await response.content.read(MAX_HTML + 1)
                if len(raw) > MAX_HTML:
                    raise ValueError("Article is too large")
                parser = ArticleParser()
                parser.feed(raw.decode(response.charset or "utf-8", errors="replace"))
                parser.close()
                return parser.result(link)
        raise ValueError("Too many redirects")


@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("url"): vol.All(str, vol.Length(min=15, max=1024)),
})
@websocket_api.async_response
async def article_read_command(hass, connection, msg):
    try:
        result = await read_public_article(msg["url"])
    except ValueError as exc:
        # Report a bounded reason without revealing private addresses or
        # source response bodies to the requesting dashboard.
        reason = str(exc)
        if reason.startswith("Article HTTP status "):
            reason = "Die Webseite antwortet mit HTTP " + reason.rsplit(" ", 1)[-1] + "."
        elif "redirect" in reason.lower():
            reason = "Die Webseite leitet zu einer nicht erlaubten Adresse weiter."
        elif "readable article" in reason.lower():
            reason = "Auf der Seite wurde kein lesbarer Artikeltext erkannt."
        else:
            reason = "Diese Quelle kann nicht sicher ausgelesen werden."
        connection.send_result(msg["id"], {"error": reason})
        return
    except (TypeError, UnicodeError, OSError, asyncio.TimeoutError, aiohttp.ClientError):
        connection.send_result(msg["id"], {"error": "Die Webseite ist gerade nicht erreichbar. Der Suchauszug bleibt verfügbar."})
        return
    connection.send_result(msg["id"], result)
