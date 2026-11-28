"""TAFA module service API: configurable, inspectable HA actions.

Service endpoints are stable contracts. No installation-specific entity IDs,
automation names, room names or URLs appear in this module.
The HA conversation entity remains the request/router module; scripts can
consume these actions without duplicating the source bindings in templates.
"""
import math
import re
from uuid import uuid4

import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.components import conversation
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import ServiceValidationError

from .const import DOMAIN, settings
from .sources import METRICS, SOURCES, UNITS
from .web_search import query_searxng

METRIC_SCHEMA = vol.Schema({vol.Required("quelle"): vol.In(tuple(METRICS))})
SEARCH_SCHEMA = vol.Schema({
    vol.Required("suchbegriff"): vol.All(str, vol.Length(min=1, max=200)),
})
INFO_SCHEMA = vol.Schema({
    vol.Required("titel"): vol.All(str, vol.Length(min=1, max=100)),
    vol.Required("nachricht"): vol.All(str, vol.Length(min=1, max=2000)),
    vol.Optional("kamera", default=""): str,
    vol.Optional("dauer", default=30): vol.All(vol.Coerce(int), vol.Range(min=5, max=180)),
    vol.Optional("request_id", default=""): str,
    vol.Optional("device_id", default=""): str,
    vol.Optional("room", default=""): str,
})
REQUEST_SCHEMA = vol.Schema({
    vol.Required("text"): vol.All(str, vol.Length(min=1, max=500)),
    vol.Optional("language", default="de"): vol.All(str, vol.Length(min=2, max=12)),
    vol.Optional("conversation_id", default=""): vol.All(str, vol.Length(max=120)),
})
SERVICES = ("anfrage_verarbeiten", "sensor_auslesen", "internet_suche", "infobox_anzeigen", "modul_status")


def register(hass, entry):
    async def read_sensor(call):
        key = call.data["quelle"]
        mapped = settings(entry).get("sources") or {}
        entity_id = mapped.get(key)
        label, allowed_units = METRICS[key]
        if not isinstance(entity_id, str) or not entity_id.startswith(SOURCES[key] + "."):
            return {"available": False, "quelle": key, "entity_id": "",
                    "text": f"{label}: Keine TAFA-Datenquelle konfiguriert."}
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable", ""):
            return {"available": False, "quelle": key, "entity_id": entity_id,
                    "text": f"{label}: Die konfigurierte Datenquelle ist nicht verfügbar."}
        unit = state.attributes.get("unit_of_measurement")
        try:
            value = float(state.state)
        except (TypeError, ValueError, OverflowError):
            value = math.nan
        if not math.isfinite(value) or unit not in allowed_units:
            return {"available": False, "quelle": key, "entity_id": entity_id,
                    "text": f"{label}: Der Wert oder seine Einheit ist ungültig."}
        shown = f"{value:.1f}".replace(".", ",")
        speech = f"{label}: {shown} {UNITS.get(unit, unit)}."
        if key == "heizoel":
            speech = f"Der aktuelle Heizölbestand beträgt laut {state.name} etwa {shown} Liter."
        return {
            "available": True, "quelle": key, "entity_id": entity_id,
            "label": label, "value": value, "unit": unit, "text": speech,
            "source_name": state.name[:120],
        }

    async def process_request(call):
        registry = er.async_get(hass)
        agent_id = registry.async_get_entity_id(
            "conversation", DOMAIN, entry.entry_id + "_conversation_router"
        )
        if not agent_id:
            raise ServiceValidationError("TAFA conversation router is not available")
        result = await conversation.async_converse(
            hass=hass, text=call.data["text"].strip(),
            conversation_id=call.data.get("conversation_id") or None,
            context=call.context, language=call.data.get("language", "de"),
            agent_id=agent_id,
        )
        payload = result.response.as_dict()
        answer = payload.get("speech", {}).get("plain", {}).get("speech", "")
        if not isinstance(answer, str):
            answer = ""
        return {
            "success": payload.get("response_type") != "error",
            "text": answer[:2000], "conversation_id": result.conversation_id,
        }

    async def search(call):
        query = call.data["suchbegriff"].strip()
        cfg = settings(entry)
        return await query_searxng(hass, cfg.get("search_base", ""), query)

    async def info(call):
        d = call.data
        camera = d.get("kamera") or ""
        if camera and (not re.fullmatch(r"camera\.[a-z0-9_]+", camera)
                       or hass.states.get(camera) is None):
            raise ServiceValidationError("Unknown camera entity")
        request_id = str(d.get("request_id") or uuid4().hex)[:100]
        payload = {
            "title": d["titel"], "message": d["nachricht"], "camera": camera,
            "seconds": d["dauer"], "request_id": request_id,
        }
        if d.get("device_id"):
            payload["device_id"] = d["device_id"][:100]
        if d.get("room"):
            payload["room"] = d["room"][:64]
        hass.bus.async_fire("tafa_infobox_show", payload, context=call.context)

    async def status(call):
        cfg = settings(entry)
        mapped = cfg.get("sources") or {}
        return {
            "modules": ["anfrage_verarbeiten", "sensor_auslesen",
                        "internet_suche", "infobox_anzeigen", "sprechen",
                        "geraet_schalten", "vision", "ambient"],
            "configured_sources": sorted(k for k in mapped if k in SOURCES),
            "missing_sources": sorted(k for k in METRICS if k not in mapped),
            "room_count": len(cfg.get("rooms") or {}),
            "voice_agent_configured": bool(cfg.get("llm_agent")),
            "event": "tafa_infobox_show",
        }

    hass.services.async_register(DOMAIN, "anfrage_verarbeiten", process_request,
                                  schema=REQUEST_SCHEMA,
                                  supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "sensor_auslesen", read_sensor,
                                  schema=METRIC_SCHEMA,
                                  supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "internet_suche", search,
                                  schema=SEARCH_SCHEMA,
                                  supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "infobox_anzeigen", info, schema=INFO_SCHEMA)
    hass.services.async_register(DOMAIN, "modul_status", status,
                                  schema=vol.Schema({}),
                                  supports_response=SupportsResponse.ONLY)


def unregister(hass):
    for service in SERVICES:
        hass.services.async_remove(DOMAIN, service)
