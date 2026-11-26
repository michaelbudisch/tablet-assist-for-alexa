"""Cross-device, installation-local TAFA dashboard configuration.

Stored by Home Assistant's Store helper, NOT as YAML, an automation, a
Lovelace storage file, or a browser-local setting. User-specific source
entity IDs never enter the distribution bundle or Git repository.
"""
import asyncio
import re

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORE_KEY = DOMAIN + "_dashboard"
STORE_VERSION = 1
PRESENTATION_DEFAULTS = {
    "captions": True, "houseCards": True, "knowledge": True,
    "knowledgeMedia": False, "contextNav": True, "search": True,
    "returnTarget": "previous", "returnSeconds": 20, "infoSeconds": 30,
}

GET_COMMAND = DOMAIN + "/dashboard/get"
SET_COMMAND = DOMAIN + "/dashboard/set"

MODULES = frozenset((
    "lights", "energy", "battery", "ev", "heating", "heatpump",
    "fuel", "appliances", "cameras", "waste", "shopping",
    "weather", "assist", "custom",
))
ROLE_DOMAINS = {
    "lights": [
        "light"
    ],
    "room_temperature": [
        "sensor"
    ],
    "grid_power": [
        "sensor"
    ],
    "home_power": [
        "sensor"
    ],
    "solar_power": [
        "sensor"
    ],
    "solar_today": [
        "sensor"
    ],
    "grid_import": [
        "sensor"
    ],
    "grid_export": [
        "sensor"
    ],
    "price": [
        "sensor"
    ],
    "solar_tomorrow": [
        "sensor"
    ],
    "battery_level": [
        "sensor"
    ],
    "battery_charge": [
        "sensor"
    ],
    "battery_discharge": [
        "sensor"
    ],
    "charger_power": [
        "sensor"
    ],
    "charger_energy": [
        "sensor"
    ],
    "charger_status": [
        "sensor",
        "binary_sensor"
    ],
    "climate": [
        "climate"
    ],
    "heating_temperature": [
        "sensor"
    ],
    "heating_status": [
        "sensor",
        "binary_sensor"
    ],
    "heatpump_power": [
        "sensor"
    ],
    "heatpump_temperature": [
        "sensor"
    ],
    "heatpump_status": [
        "sensor",
        "binary_sensor",
        "water_heater"
    ],
    "heatpump_energy": [
        "sensor"
    ],
    "heatpump_cost": [
        "sensor"
    ],
    "heatpump_remaining": [
        "sensor"
    ],
    "heatpump_finish": [
        "sensor"
    ],
    "heatpump_progress": [
        "sensor"
    ],
    "heatpump_quality": [
        "sensor"
    ],
    "fuel_percent": [
        "sensor"
    ],
    "fuel_volume": [
        "sensor"
    ],
    "fuel_usage": [
        "sensor"
    ],
    "appliance_power": [
        "sensor"
    ],
    "appliance_status": [
        "sensor",
        "binary_sensor"
    ],
    "appliance_progress": [
        "sensor"
    ],
    "appliance_energy": [
        "sensor"
    ],
    "appliance_cost": [
        "sensor"
    ],
    "appliance_finish": [
        "sensor"
    ],
    "cameras": [
        "camera"
    ],
    "waste_dates": [
        "sensor"
    ],
    "waste_calendars": [
        "calendar"
    ],
    "shopping_lists": [
        "todo"
    ],
    "weather": [
        "weather"
    ],
    "custom": [
        "sensor",
        "binary_sensor",
        "light",
        "switch",
        "climate",
        "weather",
        "media_player",
        "calendar",
        "todo",
        "number",
        "select",
        "input_boolean",
        "input_number",
        "input_text"
    ]
}
ENTITY = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")
PIPELINE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
DEFAULT_MODULES = [
    "weather", "lights", "energy", "ev", "heating", "heatpump",
    "fuel", "appliances", "cameras", "waste", "shopping", "assist",
]


def default_dashboard():
    return {
        "type": "custom:tafa-home-dashboard", "version": 1,
        "language": "auto", "theme": "dark", "accent": "teal",
        "density": "comfortable", "gridSign": "import",
        "modules": list(DEFAULT_MODULES),
        "bindings": {key: [] for key in ROLE_DOMAINS},
        "assist": {}, "title": "TAFA Dashboard",
        "presentation": dict(PRESENTATION_DEFAULTS),
    }


def validate_dashboard(raw):
    if not isinstance(raw, dict):
        raise ValueError("Dashboard must be an object")
    allowed = {"type", "version", "modules", "bindings", "assist",
               "language", "theme", "accent", "density", "gridSign", "title",
               "presentation"}
    if set(raw) - allowed:
        raise ValueError("Unsupported dashboard configuration fields")
    if raw.get("type") != "custom:tafa-home-dashboard" or raw.get("version") != 1:
        raise ValueError("Unknown TAFA dashboard version")
    result = default_dashboard()
    for name, values in {
        "language": ("auto", "de", "en"),
        "theme": ("dark", "light", "ha"),
        "accent": ("teal", "blue", "violet"),
        "density": ("comfortable", "compact"),
        "gridSign": ("import", "export"),
    }.items():
        value = raw.get(name, result[name])
        if value not in values:
            raise ValueError("Unsupported dashboard " + name)
        result[name] = value
    title = raw.get("title", result["title"])
    if not isinstance(title, str) or len(title) > 60:
        raise ValueError("Dashboard title too long")
    result["title"] = title
    modules = raw.get("modules", result["modules"])
    if (not isinstance(modules, list) or len(modules) > len(MODULES)
            or any(not isinstance(x, str) or x not in MODULES for x in modules)
            or len(set(modules)) != len(modules)):
        raise ValueError("Invalid dashboard modules")
    result["modules"] = list(modules)
    bindings = raw.get("bindings", {})
    if not isinstance(bindings, dict) or set(bindings) - ROLE_DOMAINS.keys():
        raise ValueError("Invalid dashboard entity roles")
    for name, allowed_domains in ROLE_DOMAINS.items():
        entities = bindings.get(name, [])
        if (not isinstance(entities, list) or len(entities) > 100
                or len(set(x for x in entities if isinstance(x, str))) != len(entities)):
            raise ValueError("Invalid entity mapping for " + name)
        for entity in entities:
            if (not isinstance(entity, str) or len(entity) > 255
                    or not ENTITY.fullmatch(entity)
                    or entity.split(".", 1)[0] not in allowed_domains):
                raise ValueError("Invalid entity domain for " + name)
        result["bindings"][name] = list(entities)
    assist = raw.get("assist", {})
    if not isinstance(assist, dict) or set(assist) - {"pipeline_id", "wake_pipeline_id"}:
        raise ValueError("Invalid Assist profile")
    for key, val in assist.items():
        if not isinstance(val, str) or (val and not PIPELINE.fullmatch(val)):
            raise ValueError("Invalid Assist pipeline ID")
        result["assist"][key] = val
    presentation = raw.get("presentation", {})
    if not isinstance(presentation, dict) or set(presentation) - PRESENTATION_DEFAULTS.keys():
        raise ValueError("Invalid dashboard presentation options")
    for key, default in PRESENTATION_DEFAULTS.items():
        value = presentation.get(key, default)
        if isinstance(default, bool):
            if type(value) is not bool:
                raise ValueError("Invalid presentation toggle " + key)
        elif key == "returnTarget":
            if value not in ("previous", "start"):
                raise ValueError("Invalid return target")
        elif type(value) is not int or not 5 <= value <= 180:
            raise ValueError("Invalid presentation duration " + key)
        result["presentation"][key] = value
    return result


def migrate_saved_dashboard(raw):
    """Recover known settings individually without rewriting the stored original.

    New modules and source roles always come from current defaults. Old modules,
    entity assignments, preferences and module order survive whenever valid.
    Unsupported legacy fields are ignored here but remain in the original HA
    Store until an explicit save; that save first snapshots the original.
    """
    if not isinstance(raw, dict):
        return default_dashboard()
    if raw.get("type") not in (None, "custom:tafa-home-dashboard"):
        return default_dashboard()
    if isinstance(raw.get("version"), int) and raw["version"] > 1:
        # A newer TAFA version wrote this: do not silently overwrite it.
        raise ValueError("Newer TAFA dashboard schema detected; update TAFA")
    defaults = default_dashboard()
    clean = {"type": defaults["type"], "version": defaults["version"]}
    for key in ("language", "theme", "accent", "density", "gridSign", "title"):
        value = raw.get(key)
        if value is not None:
            trial = {**defaults, key: value}
            try:
                validate_dashboard(trial)
            except (TypeError, ValueError):
                continue
            clean[key] = value
    modules = raw.get("modules")
    if isinstance(modules, list):
        clean["modules"] = list(dict.fromkeys(
            k for k in modules if isinstance(k, str) and k in MODULES))
    bindings = raw.get("bindings")
    if isinstance(bindings, dict):
        migrated = {}
        for role, domains in ROLE_DOMAINS.items():
            ids = bindings.get(role)
            if not isinstance(ids, list):
                continue
            filtered = []
            for item in ids:
                if (isinstance(item, str) and len(item) <= 255
                        and ENTITY.fullmatch(item)
                        and item.split(".", 1)[0] in domains
                        and item not in filtered):
                    filtered.append(item)
                if len(filtered) >= 100:
                    break
            migrated[role] = filtered
        clean["bindings"] = migrated
    assist = raw.get("assist")
    if isinstance(assist, dict):
        clean["assist"] = {k: v for k, v in assist.items()
                           if k in ("pipeline_id", "wake_pipeline_id")
                           and isinstance(v, str) and (not v or PIPELINE.fullmatch(v))}
    prefs = raw.get("presentation")
    if isinstance(prefs, dict):
        migrated_prefs = {}
        for key, default in PRESENTATION_DEFAULTS.items():
            value = prefs.get(key)
            if type(default) is bool and type(value) is bool:
                migrated_prefs[key] = value
            elif key == "returnTarget" and value in ("previous", "start"):
                migrated_prefs[key] = value
            elif type(default) is int and type(value) is int and 5 <= value <= 180:
                migrated_prefs[key] = value
        clean["presentation"] = migrated_prefs
    return validate_dashboard(clean)


def dashboard_store(hass):
    return Store(hass, STORE_VERSION, STORE_KEY)


def dashboard_backup_store(hass):
    # Separate HA Store key, not the raw .storage file or Lovelace YAML.
    return Store(hass, STORE_VERSION, STORE_KEY + "_previous")


async def load_dashboard(hass):
    data = await dashboard_store(hass).async_load()
    if data is None:
        return default_dashboard()
    try:
        return validate_dashboard(data)
    except (TypeError, ValueError):
        return migrate_saved_dashboard(data)


@websocket_api.websocket_command({
    vol.Required("type"): GET_COMMAND,
})
@websocket_api.async_response
async def async_get_dashboard(hass, connection, msg):
    connection.send_result(msg["id"], {"config": await load_dashboard(hass)})


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"): SET_COMMAND,
    vol.Required("config"): dict,
})
@websocket_api.async_response
async def async_set_dashboard(hass, connection, msg):
    try:
        parsed = validate_dashboard(msg["config"])
    except (ValueError, TypeError) as exc:
        connection.send_error(msg["id"], "invalid_dashboard", str(exc)[:180])
        return
    lock = hass.data.setdefault(DOMAIN, {}).setdefault(
        "dashboard_write_lock", asyncio.Lock())
    async with lock:
        existing = await dashboard_store(hass).async_load()
        if existing is not None and existing != parsed:
            # Snapshot before overwriting. Includes unknown future/legacy keys.
            await dashboard_backup_store(hass).async_save(existing)
        await dashboard_store(hass).async_save(parsed)
    connection.send_result(msg["id"], {"saved": True, "config": parsed})
