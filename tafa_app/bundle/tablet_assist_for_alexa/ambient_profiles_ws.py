"""Per-device TAFA Ambient profiles stored centrally in Home Assistant.

Only registered device owners or HA administrators may access their profiles.
The API exposes no device tokens or microphone/audio data. Revisions prevent
overwriting a profile edited concurrently in another browser.
"""
import asyncio
import re

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .relay.relay_wake_devices import KEY

COMMAND = DOMAIN + "/ambient_profiles"
STORE_KEY = DOMAIN + "_ambient_profiles"
DEVICE_ID = re.compile(r"^[a-f0-9]{32}$")
METRIC_ID = re.compile(r"^(sensor|binary_sensor|number|input_number)\.[a-z0-9_]+$")
CALENDAR_ID = re.compile(r"^calendar\.[a-z0-9_]+$")
PRESENCE_ID = re.compile(r"^(sensor|binary_sensor)\.[a-z0-9_]+$")
UPDATE_EVENT = "tafa_ambient_profile_updated"


def defaults():
    return {
        "calendar": "", "presence": "", "dismiss": "sensor",
        "idle": 55, "enabled": True, "autoOpen": True, "metrics": None,
    }


def validate_profile(raw):
    if not isinstance(raw, dict) or set(raw) - set(defaults()):
        raise ValueError("Unsupported Ambient configuration")
    cfg = {**defaults(), **raw}
    for field, pattern in (("calendar", CALENDAR_ID), ("presence", PRESENCE_ID)):
        value = cfg[field]
        if not isinstance(value, str) or (value and not pattern.fullmatch(value)):
            raise ValueError("Invalid " + field + " entity")
    if cfg["dismiss"] not in ("sensor", "time", "either"):
        raise ValueError("Invalid close behavior")
    duration = cfg["idle"]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not 0 <= duration <= 86400:
        raise ValueError("Invalid display duration")
    for toggle in ("enabled", "autoOpen"):
        if type(cfg[toggle]) is not bool:
            raise ValueError("Invalid " + toggle)
    metrics = cfg["metrics"]
    if metrics is not None:
        if not isinstance(metrics, list) or len(metrics) > 12:
            raise ValueError("Invalid sensor list")
        clean = []
        for item in metrics:
            if not isinstance(item, dict) or set(item) - {"id", "name"}:
                raise ValueError("Invalid sensor entry")
            identifier, name = item.get("id"), item.get("name")
            if not isinstance(identifier, str) or not METRIC_ID.fullmatch(identifier):
                raise ValueError("Invalid sensor entity ID")
            if not isinstance(name, str) or len(name) > 40:
                raise ValueError("Invalid sensor label")
            clean.append({"id": identifier, "name": name})
        cfg["metrics"] = clean
    return cfg


async def _load(hass):
    raw = await Store(hass, 1, STORE_KEY).async_load()
    if not isinstance(raw, dict) or not isinstance(raw.get("profiles"), dict):
        return {"profiles": {}}
    return raw


@websocket_api.websocket_command({
    vol.Required("type"): COMMAND,
    vol.Required("action"): vol.In(("list", "get", "save", "subscribe")),
    vol.Optional("device_id"): str,
    vol.Optional("profile"): dict,
    vol.Optional("revision"): vol.All(vol.Coerce(int), vol.Range(min=0)),
})
@websocket_api.async_response
async def ambient_profiles_command(hass, connection, msg):
    user = connection.user
    controller = hass.data.get(DOMAIN, {}).get(KEY)
    if not user or not user.is_active:
        connection.send_error(msg["id"], "unauthorized", "Inactive HA user")
        return
    if controller is None:
        connection.send_error(msg["id"], "not_ready", "TAFA device registry unavailable")
        return

    action = msg["action"]
    if action == "list":
        saved = await _load(hass)
        devices = []
        for device in controller.devices.values():
            if not controller.allowed(user, device):
                continue
            identifier = device["device_id"]
            record = saved["profiles"].get(identifier, {})
            public = controller.public(device)
            devices.append({
                "device_id": identifier,
                "room": str(device.get("room") or "Tablet"),
                "label": "TAFA · " + str(device.get("room") or "Tablet"),
                "online": bool(public.get("online")),
                "has_profile": isinstance(record.get("profile"), dict),
                "revision": int(record.get("revision", 0)),
            })
        connection.send_result(msg["id"], {
            "devices": sorted(devices, key=lambda x: (x["room"].casefold(), x["device_id"]))
        })
        return

    identifier = msg.get("device_id", "")
    if not isinstance(identifier, str) or not DEVICE_ID.fullmatch(identifier):
        connection.send_error(msg["id"], "invalid_device", "Invalid TAFA device ID")
        return
    device = controller.devices.get(identifier)
    if not device or not controller.allowed(user, device):
        connection.send_error(msg["id"], "unauthorized", "Device not registered or not permitted")
        return

    if action == "subscribe":
        @callback
        def updated(event):
            if event.data.get("device_id") != identifier:
                return
            current = controller.devices.get(identifier)
            if not current or not controller.allowed(user, current):
                return
            connection.send_event(msg["id"], {
                "device_id": identifier, "revision": event.data.get("revision", 0)
            })

        unsubscribe = hass.bus.async_listen(UPDATE_EVENT, updated)
        connection.subscriptions[msg["id"]] = unsubscribe
        connection.send_result(msg["id"], {"subscribed": True})
        return

    if action == "get":
        saved = await _load(hass)
        record = saved["profiles"].get(identifier, {})
        connection.send_result(msg["id"], {
            "device_id": identifier,
            "revision": int(record.get("revision", 0)),
            "profile": record.get("profile") if isinstance(record.get("profile"), dict) else None,
        })
        return

    if "profile" not in msg or "revision" not in msg:
        connection.send_error(msg["id"], "invalid_request", "Profile and revision are required")
        return
    try:
        profile = validate_profile(msg["profile"])
    except (ValueError, TypeError) as error:
        connection.send_error(msg["id"], "invalid_profile", str(error)[:180])
        return

    lock = hass.data.setdefault(DOMAIN, {}).setdefault("ambient_profiles_lock", asyncio.Lock())
    async with lock:
        saved = await _load(hass)
        current = saved["profiles"].get(identifier, {})
        revision = int(current.get("revision", 0))
        if revision != msg["revision"]:
            connection.send_error(msg["id"], "conflict", "Profile changed elsewhere; reload it")
            return
        new_revision = revision + 1
        saved["profiles"][identifier] = {"revision": new_revision, "profile": profile}
        await Store(hass, 1, STORE_KEY).async_save(saved)

    hass.bus.async_fire(UPDATE_EVENT, {"device_id": identifier, "revision": new_revision})
    connection.send_result(msg["id"], {
        "saved": True, "device_id": identifier,
        "revision": new_revision, "profile": profile,
    })
