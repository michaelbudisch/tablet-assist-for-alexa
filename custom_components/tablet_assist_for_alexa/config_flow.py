"""Configure the integration without editing source files or YAML."""
import json
import re
from urllib.parse import urlsplit

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PROFILES, ROOMS

def origin(value, https_only=False):
    value = value.strip().rstrip("/")
    u = urlsplit(value)
    if (u.scheme not in (("https",) if https_only else ("http", "https"))
            or not u.hostname or u.username is not None or u.password is not None
            or u.path or u.query or u.fragment
            or not re.fullmatch(r"[A-Za-z0-9.-]+", u.hostname)
            or not re.fullmatch(r"https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?", value)):
        raise ValueError("Invalid origin")
    if u.port is not None and not 1 <= u.port <= 65535:
        raise ValueError("Invalid port")
    return value

def room_map(raw):
    obj = json.loads(raw or "{}")
    if not isinstance(obj, dict) or any(k not in ROOMS for k in obj):
        raise ValueError("Invalid rooms")
    for item in obj.values():
        if not isinstance(item, dict) or set(item) - {"notify", "dnd", "quiet"} or not item.get("notify"):
            raise ValueError("Invalid room")
        for field, domain in (("notify", "notify"), ("dnd", "switch"), ("quiet", "schedule")):
            if field in item and (not isinstance(item[field], str) or not re.fullmatch(domain + r"\.[a-z0-9_]+", item[field])):
                raise ValueError("Invalid entity")
    return obj

def translated_select(key, options):
    # Preserve existing stored values and the speech-server API.
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=options, translation_key=key, mode=selector.SelectSelectorMode.DROPDOWN))

def schema():
    password = selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD))
    return vol.Schema({
        vol.Required("piper_base", default="http://speechserver.local:5000"): str,
        vol.Required("cpu_stt"): selector.EntitySelector(selector.EntitySelectorConfig(domain="stt")),
        vol.Optional("gpu_base", default=""): str,
        vol.Optional("qwen_token", default=""): password,
        vol.Optional("gpu_stt"): selector.EntitySelector(selector.EntitySelectorConfig(domain="stt")),
        vol.Optional("gpu_stt_host", default=""): str,
        vol.Optional("llm_agent"): selector.EntitySelector(selector.EntitySelectorConfig(domain="conversation")),
        vol.Required("hardware_profile", default="Automatisch"): translated_select("hardware_profile", ["Automatisch", "Homeserver"]),
        vol.Required("live_profile", default="Natürlich"): translated_select("live_profile", list(PROFILES)),
        vol.Required("voice_variant", default="default"): translated_select("voice_variant", ["default", *map(str, range(1, 10))]),
        vol.Required("conversation_mode", default="Intelligent"): translated_select("conversation_mode", ["Manuell", "Intelligent", "Automatisch"]),
        vol.Optional("mp3_base", default=""): str,
        vol.Optional("mp3_token", default=""): password,
        vol.Optional("public_audio_base", default=""): str,
        vol.Optional("rooms_json", default="{}"): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        vol.Required("mp3_profile", default="Natürlich"): translated_select("mp3_profile", ["Natürlich", "Studio", "Durchsage"]),
        vol.Required("chime", default=False): bool,
    })

class TabletAssistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _form(self, step, user_input, existing=None):
        errors = {}
        if user_input is not None:
            data = {**user_input}
            for key in ("gpu_base", "qwen_token", "gpu_stt", "gpu_stt_host", "llm_agent",
                        "mp3_base", "mp3_token", "public_audio_base", "rooms_json"):
                data[key] = (data.get(key) or "").strip()
            try:
                data["piper_base"] = origin(data["piper_base"])
                for key in ("gpu_base", "mp3_base", "public_audio_base"):
                    if data[key]:
                        data[key] = origin(data[key], key == "public_audio_base")
                if data["gpu_stt_host"] and not re.fullmatch(r"[A-Za-z0-9.-]+", data["gpu_stt_host"]):
                    raise ValueError("Invalid host")
                if data["gpu_base"] and len(data["qwen_token"]) < 32:
                    raise ValueError("Missing GPU token")
                data["rooms"] = room_map(data["rooms_json"])
                if data["rooms"] and not (data["mp3_base"] and data["public_audio_base"] and len(data["mp3_token"]) >= 32):
                    raise ValueError("Missing announcement configuration")
                registry = er.async_get(self.hass)
                for key in ("cpu_stt", "gpu_stt"):
                    if data.get(key):
                        ent = registry.async_get(data[key])
                        if ent is None or ent.platform != "wyoming":
                            raise ValueError("Select a Wyoming STT entity")
                if data["gpu_stt"] and data["gpu_stt"] == data["cpu_stt"]:
                    raise ValueError("Select distinct STT providers")
                if data["llm_agent"]:
                    ent = registry.async_get(data["llm_agent"])
                    if ent and ent.platform == DOMAIN:
                        raise ValueError("Recursive conversation agent")
            except (ValueError, TypeError, KeyError):
                errors["base"] = "invalid_configuration"
            if not errors:
                try:
                    session = async_get_clientsession(self.hass)
                    async with session.get(data["piper_base"] + "/health",
                                           timeout=aiohttp.ClientTimeout(total=4),
                                           allow_redirects=False) as response:
                        if response.status != 200 or not (await response.json()).get("ready"):
                            raise ValueError("Piper not ready")
                except (aiohttp.ClientError, TimeoutError, ValueError, AttributeError):
                    errors["base"] = "cannot_connect"
            if not errors:
                if existing is not None:
                    return self.async_update_reload_and_abort(existing, data=data)
                return self.async_create_entry(title="Tablet Assist for Alexa", data=data)
        suggested = user_input if user_input is not None else (dict(existing.data) if existing else {})
        suggested = {k:v for k,v in suggested.items() if k != "rooms" and v != ""}
        return self.async_show_form(step_id=step, data_schema=self.add_suggested_values_to_schema(schema(), suggested), errors=errors)

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return await self._form("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._form("reconfigure", user_input, self._get_reconfigure_entry())
