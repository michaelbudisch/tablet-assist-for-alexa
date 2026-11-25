"""App-only configuration sync. The Supervisor App is the single settings owner.

No credentials are accepted. The command requires an HA admin session AND an
App-managed installed integration. Marketplace installations retain their flow.
"""
import json
import re
from pathlib import Path

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers import entity_registry as er

from .config_flow import CHOICES, origin, room_map
from .const import DOMAIN
from .sources import SOURCES

COMMAND = DOMAIN + "/sync_app_configuration"
APP_MANAGED_MARKER = ".tafa-managed.json"


def parse_settings(raw, registry):
    """Defensive validation of the data generated from /data/options.json."""
    if not isinstance(raw, dict):
        raise ValueError("Expected TAFA App settings object")
    result = {"piper_base": origin(raw["piper_base"])}
    for key in ("gpu_base", "mp3_base", "public_audio_base"):
        value = raw.get(key, "")
        if not isinstance(value, str):
            raise ValueError("URL must be text")
        result[key] = origin(value, key == "public_audio_base") if value else ""
    for key in ("hardware_profile", "live_profile", "mp3_profile", "conversation_mode"):
        slug = raw.get(key)
        if slug not in CHOICES[key]:
            raise ValueError("Invalid " + key)
        result[key] = CHOICES[key][slug]
    variant = raw.get("voice_variant", "default")
    if variant not in ("default", *map(str, range(1, 10))):
        raise ValueError("Invalid voice variant")
    result["voice_variant"] = variant
    for key in ("chime", "reminders_enabled", "learning_enabled"):
        value = raw.get(key, False)
        if not isinstance(value, bool):
            raise ValueError("Expected bool for " + key)
        result[key] = value
    for key in ("cpu_stt", "gpu_stt", "llm_agent"):
        value = raw.get(key, "")
        if not isinstance(value, str):
            raise ValueError("Invalid HA entity")
        domain = "conversation" if key == "llm_agent" else "stt"
        if value and not re.fullmatch(domain + r"\.[a-z0-9_]+", value):
            raise ValueError("Invalid HA entity")
        if value and key != "llm_agent":
            entity = registry.async_get(value)
            if entity is None or entity.platform != "wyoming":
                raise ValueError("Choose an existing Wyoming STT entity")
        if value and key == "llm_agent":
            entity = registry.async_get(value)
            if entity is not None and entity.platform == DOMAIN:
                raise ValueError("Cannot use own TAFA conversation router as LLM")
        result[key] = value
    if result["gpu_stt"] and result["gpu_stt"] == result["cpu_stt"]:
        raise ValueError("Separate CPU/GPU Wyoming entities required")
    host = raw.get("gpu_stt_host", "")
    if not isinstance(host, str) or (host and not re.fullmatch(r"[A-Za-z0-9.-]+", host)):
        raise ValueError("Invalid GPU STT host")
    result["gpu_stt_host"] = host
    rooms = room_map(raw.get("rooms_json", "{}"))
    result["rooms_json"] = json.dumps(rooms, ensure_ascii=False)
    result["rooms"] = rooms
    if rooms and not (result["mp3_base"] and result["public_audio_base"]):
        raise ValueError("Room announcements need MP3 and HTTPS")
    sources = json.loads(raw.get("sources_json", "{}") or "{}")
    if not isinstance(sources, dict) or set(sources) - set(SOURCES):
        raise ValueError("Unknown data sources")
    for key, entity in sources.items():
        if not isinstance(entity, str) or not re.fullmatch(SOURCES[key] + r"\.[a-z0-9_]+", entity):
            raise ValueError("Invalid data source entity")
    result["sources"] = sources
    room = raw.get("reminder_room", "")
    if not isinstance(room, str) or (room and room not in rooms):
        raise ValueError("Reminder room missing from Alexa rooms")
    result["reminder_room"] = room
    return result


def _unique_wyoming_stt(registry):
    """Auto-select STT only when there is exactly one eligible Wyoming provider."""
    items = [
        entity.entity_id for entity in registry.entities.values()
        if entity.platform == "wyoming" and entity.entity_id.startswith("stt.")
        and not entity.disabled_by
    ]
    return items[0] if len(items) == 1 else ""


def merge_settings(entry, values, registry):
    """One-time non-destructive migration, then App options are authoritative."""
    previous = {**entry.data, **entry.options}
    first_sync = not entry.options.get("tafa_app_managed", False)
    result = dict(entry.options)
    # Existing advanced configuration is retained during the first migration
    # when its newly-added App fields still hold empty defaults.
    for key, value in values.items():
        if first_sync and key in {
            "cpu_stt", "gpu_stt", "gpu_stt_host", "llm_agent", "reminder_room"
        } and not value and previous.get(key):
            continue
        if first_sync and key in {"rooms", "sources"} and not value and previous.get(key):
            continue
        if first_sync and key in {"rooms_json", "sources_json"} and value == "{}" and previous.get(key):
            continue
        if first_sync and key in {"learning_enabled", "reminders_enabled"} and value is False and previous.get(key):
            continue
        result[key] = value
    if not result.get("cpu_stt"):
        detected = _unique_wyoming_stt(registry)
        if detected:
            result["cpu_stt"] = detected
    if result.get("cpu_stt") and result.get("gpu_stt") == result["cpu_stt"]:
        raise ValueError("CPU and GPU STT must differ")
    if result.get("reminder_room") and result["reminder_room"] not in result.get("rooms", {}):
        raise ValueError("Reminder room is not configured")
    result["tafa_app_managed"] = True
    return result


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("settings"): dict,
})
@websocket_api.async_response
async def async_sync_from_app(hass, connection, msg):
    """Apply only validated settings to the App's own integration."""
    if not (Path(__file__).parent / APP_MANAGED_MARKER).is_file():
        connection.send_error(msg["id"], "not_managed", "Install TAFA through the App first")
        return
    entries = hass.config_entries.async_entries(DOMAIN)
    if len(entries) != 1:
        connection.send_error(msg["id"], "not_configured", "Exactly one TAFA integration required")
        return
    try:
        registry = er.async_get(hass)
        changes = merge_settings(entries[0], parse_settings(msg["settings"], registry), registry)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        connection.send_error(msg["id"], "invalid_settings", str(exc)[:160])
        return
    changed = changes != entries[0].options
    if changed:
        hass.config_entries.async_update_entry(entries[0], options=changes)
    connection.send_result(msg["id"], {"changed": changed, "managed_by": "TAFA App"})
