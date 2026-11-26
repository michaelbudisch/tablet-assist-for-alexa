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
from .sources import SOURCES

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
    if not isinstance(obj, dict) or len(obj) > 32 or any(not isinstance(k, str) or not 1 <= len(k) <= 48 or not re.fullmatch(r"[\w äöüÄÖÜß-]+", k) or k != k.strip() for k in obj):
        raise ValueError("Invalid rooms")
    for item in obj.values():
        if not isinstance(item, dict) or set(item) - {"notify", "dnd", "quiet"} or not item.get("notify"):
            raise ValueError("Invalid room")
        for field, domain in (("notify", "notify"), ("dnd", "switch"), ("quiet", "schedule")):
            if field in item and (not isinstance(item[field], str) or not re.fullmatch(domain + r"\.[a-z0-9_]+", item[field])):
                raise ValueError("Invalid entity")
    return obj

CHOICES = {
    "hardware_profile": {
        "automatic": "Automatisch",
        "cpu": "Homeserver"
    },
    "live_profile": {
        "natural": "Natürlich",
        "studio": "Studio",
        "clear": "Klar"
    },
    "conversation_mode": {
        "manual": "Manuell",
        "intelligent": "Intelligent",
        "automatic": "Automatisch"
    },
    "mp3_profile": {
        "natural": "Natürlich",
        "studio": "Studio",
        "announcement": "Durchsage"
    }
}

def translated_select(key, options):
    # Preserve existing stored values and the speech-server API.
    return selector.SelectSelector(selector.SelectSelectorConfig(
        options=options, translation_key=key, mode=selector.SelectSelectorMode.DROPDOWN))

def schema():
    return vol.Schema({
        vol.Required("piper_base", default="http://speechserver.local:5000"): str,
        vol.Optional("dashboard_only", default=False): bool,
        vol.Optional("cpu_stt"): selector.EntitySelector(selector.EntitySelectorConfig(domain="stt")),
        vol.Optional("gpu_base", default=""): str,
        vol.Optional("gpu_stt"): selector.EntitySelector(selector.EntitySelectorConfig(domain="stt")),
        vol.Optional("gpu_stt_host", default=""): str,
        vol.Optional("llm_agent"): selector.EntitySelector(selector.EntitySelectorConfig(domain="conversation")),
        vol.Required("hardware_profile", default="automatic"): translated_select("hardware_profile", list(CHOICES["hardware_profile"])),
        vol.Required("live_profile", default="natural"): translated_select("live_profile", list(CHOICES["live_profile"])),
        vol.Required("voice_variant", default="default"): translated_select("voice_variant", ["default", *map(str, range(1, 10))]),
        vol.Required("conversation_mode", default="intelligent"): translated_select("conversation_mode", list(CHOICES["conversation_mode"])),
        vol.Optional("mp3_base", default=""): str,
        vol.Optional("public_audio_base", default=""): str,
        vol.Optional("rooms_json", default="{}"): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        vol.Required("mp3_profile", default="natural"): translated_select("mp3_profile", list(CHOICES["mp3_profile"])),
        vol.Required("chime", default=False): bool,
    })

class TabletAssistConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return TabletAssistSourcesFlow()

    async def _form(self, step, user_input, existing=None):
        errors = {}
        if user_input is not None:
            data = {**user_input}
            data["cpu_stt"] = (data.get("cpu_stt") or "").strip()
            for key, choices in CHOICES.items():
                data[key] = choices.get(data.get(key), data.get(key))
            for key in ("gpu_base", "gpu_stt", "gpu_stt_host", "llm_agent",
                        "mp3_base", "public_audio_base", "rooms_json"):
                data[key] = (data.get(key) or "").strip()
            try:
                data["piper_base"] = origin(data["piper_base"])
                for key in ("gpu_base", "mp3_base", "public_audio_base"):
                    if data[key]:
                        data[key] = origin(data[key], key == "public_audio_base")
                if data["gpu_stt_host"] and not re.fullmatch(r"[A-Za-z0-9.-]+", data["gpu_stt_host"]):
                    raise ValueError("Invalid host")
                data["rooms"] = room_map(data["rooms_json"])
                if data["rooms"] and not (data["mp3_base"] and data["public_audio_base"]):
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
            # Dashboard-only first install is explicitly selected; normal
            # voice setup continues to require Piper /health readiness.
            if not errors and not data.get("dashboard_only", False):
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
        for key, choices in CHOICES.items():
            if key in suggested:
                suggested[key] = next((slug for slug, old in choices.items() if old == suggested[key]), suggested[key])
        return self.async_show_form(step_id=step, data_schema=self.add_suggested_values_to_schema(schema(), suggested), errors=errors)

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return await self._form("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        if self._get_reconfigure_entry().options.get("tafa_app_managed"):
            return self.async_abort(reason="app_configuration_only")
        return await self._form("reconfigure", user_input, self._get_reconfigure_entry())

class TabletAssistSourcesFlow(config_entries.OptionsFlow):
    """Separate everyday hardware, announcements and optional home-data sources.

    Options override entry.data via settings(entry). This preserves existing
    config entries and triggers their usual reload listener after saving.
    """

    def _values(self):
        return {**self.config_entry.data, **self.config_entry.options}

    def _save(self, changes):
        return self.async_create_entry(
            title="", data={**self.config_entry.options, **changes}
        )

    async def async_step_init(self, user_input=None):
        if self.config_entry.options.get("tafa_app_managed"):
            return self.async_abort(reason="app_configuration_only")
        # Marketplace-only users retain their choices. A blank dict must NOT
        # unexpectedly open Data sources instead of the section menu.
        if user_input:
            return await self.async_step_sources(user_input)
        return self.async_show_menu(
            step_id="init", menu_options=["hardware", "announcements", "sources"]
        )

    async def async_step_hardware(self, user_input=None):
        old = self._values()
        errors = {}
        if user_input is not None:
            new = {}
            try:
                new["piper_base"] = origin(
                    str(user_input.get("piper_base") or old.get("piper_base") or "")
                )
                new["cpu_stt"] = str(user_input.get("cpu_stt", old.get("cpu_stt", "")) or "").strip()
                new["gpu_base"] = (
                    origin(str(user_input.get("gpu_base", old.get("gpu_base"))))
                    if user_input.get("gpu_base", old.get("gpu_base")) else ""
                )
                new["gpu_stt"] = str(user_input.get("gpu_stt", old.get("gpu_stt", "")) or "").strip()
                new["gpu_stt_host"] = str(user_input.get("gpu_stt_host", old.get("gpu_stt_host", "")) or "").strip()
                new["llm_agent"] = str(user_input.get("llm_agent", old.get("llm_agent", "")) or "").strip()
                slug = user_input.get("hardware_profile", next(
                    (k for k,v in CHOICES["hardware_profile"].items()
                     if v == old.get("hardware_profile")), "automatic"))
                if slug not in CHOICES["hardware_profile"]:
                    raise ValueError("Invalid hardware profile")
                new["hardware_profile"] = CHOICES["hardware_profile"][slug]
                if new["gpu_stt_host"] and not re.fullmatch(
                    r"[A-Za-z0-9.-]+", new["gpu_stt_host"]
                ):
                    raise ValueError("Invalid GPU STT host")
                reg = er.async_get(self.hass)
                for key in ("cpu_stt", "gpu_stt"):
                    if new[key]:
                        entity = reg.async_get(new[key])
                        if entity is None or entity.platform != "wyoming":
                            raise ValueError("Choose existing Wyoming STT entity")
                if new["gpu_stt"] and new["gpu_stt"] == new["cpu_stt"]:
                    raise ValueError("Choose separate CPU and GPU STT providers")
                if new["llm_agent"]:
                    entity = reg.async_get(new["llm_agent"])
                    if entity and entity.platform == DOMAIN:
                        raise ValueError("Recursive conversation agent")
            except (ValueError, TypeError, KeyError):
                errors["base"] = "invalid_configuration"
            if not errors:
                return self._save(new)

        default_mode = next(
            (k for k,v in CHOICES["hardware_profile"].items()
             if v == old.get("hardware_profile")), "automatic"
        )
        fields = vol.Schema({
            vol.Required("piper_base", default=old.get("piper_base", "http://speechserver.local:5000")): str,
            vol.Optional("cpu_stt"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="stt")),
            vol.Required("hardware_profile", default=default_mode):
                translated_select("hardware_profile", list(CHOICES["hardware_profile"])),
            vol.Optional("gpu_base"): str,
            vol.Optional("gpu_stt"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="stt")),
            vol.Optional("gpu_stt_host"): str,
            vol.Optional("llm_agent"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="conversation")),
        })
        defaults = {
            k: old[k] for k in
            ("cpu_stt", "gpu_base", "gpu_stt", "gpu_stt_host", "llm_agent")
            if old.get(k)
        }
        return self.async_show_form(
            step_id="hardware", data_schema=self.add_suggested_values_to_schema(
                fields, defaults), errors=errors
        )

    async def async_step_announcements(self, user_input=None):
        old = self._values()
        errors = {}
        if user_input is not None:
            try:
                data = {}
                for key in ("mp3_base", "public_audio_base"):
                    value = str(user_input.get(key, old.get(key, "")) or "").strip()
                    data[key] = origin(value, key == "public_audio_base") if value else ""
                data["rooms_json"] = str(user_input.get("rooms_json", old.get("rooms_json") or json.dumps(old.get("rooms", {}), ensure_ascii=False)) or "{}")
                data["rooms"] = room_map(data["rooms_json"])
                profile = user_input.get("mp3_profile", next(
                    (k for k,v in CHOICES["mp3_profile"].items()
                     if v == old.get("mp3_profile")), "natural"))
                if profile not in CHOICES["mp3_profile"]:
                    raise ValueError("Invalid announcement profile")
                data["mp3_profile"] = CHOICES["mp3_profile"][profile]
                data["chime"] = bool(user_input.get("chime", old.get("chime", False)))
                if data["rooms"] and not (
                    data["mp3_base"] and data["public_audio_base"]
                ):
                    raise ValueError("Missing MP3 generator or HTTPS proxy")
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                errors["base"] = "invalid_configuration"
            if not errors:
                return self._save(data)

        choice = next(
            (k for k,v in CHOICES["mp3_profile"].items()
             if v == old.get("mp3_profile")), "natural"
        )
        fields = vol.Schema({
            vol.Optional("mp3_base"): str,
            vol.Optional("public_audio_base"): str,
            vol.Optional("rooms_json"): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)),
            vol.Required("mp3_profile", default=choice):
                translated_select("mp3_profile", list(CHOICES["mp3_profile"])),
            vol.Required("chime", default=bool(old.get("chime",False))): bool,
        })
        suggested = {
            k: old[k] for k in ("mp3_base", "public_audio_base")
            if old.get(k)
        }
        suggested["rooms_json"] = (
            old.get("rooms_json") or
            json.dumps(old.get("rooms", {}), ensure_ascii=False)
        )
        return self.async_show_form(
            step_id="announcements",
            data_schema=self.add_suggested_values_to_schema(fields,suggested),
            errors=errors
        )

    async def async_step_sources(self, user_input=None):
        errors={}
        if user_input is not None:
            sources={k:user_input[k] for k in SOURCES if user_input.get(k)}
            if any(not isinstance(v,str) or not v.startswith(SOURCES[k]+".") for k,v in sources.items()):
                errors["base"]="invalid_configuration"
            else:
                room=user_input.get("reminder_room","")
                allowed=self._values().get("rooms",{})
                if room and room not in allowed:
                    errors["base"]="invalid_configuration"
                else:
                    return self._save({
                        "sources": sources,
                        "learning_enabled": bool(user_input.get("learning_enabled")),
                        "reminders_enabled": bool(user_input.get("reminders_enabled")),
                        "reminder_room": room
                    })
        old=self.config_entry.options
        values={**old.get("sources",{}),
                "learning_enabled":old.get("learning_enabled",False),
                "reminders_enabled":old.get("reminders_enabled",False),
                "reminder_room":old.get("reminder_room","")}
        fields={vol.Optional(k):selector.EntitySelector(
            selector.EntitySelectorConfig(domain=domain)) for k,domain in SOURCES.items()}
        fields[vol.Required("reminders_enabled",default=False)]=bool
        fields[vol.Required("learning_enabled",default=False)]=bool
        rooms=self._values().get("rooms",{})
        fields[vol.Optional("reminder_room")]=selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(rooms),mode=selector.SelectSelectorMode.DROPDOWN)
        ) if rooms else str
        return self.async_show_form(
            step_id="sources",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields),{k:v for k,v in values.items() if v!=""}
            ),errors=errors
        )
