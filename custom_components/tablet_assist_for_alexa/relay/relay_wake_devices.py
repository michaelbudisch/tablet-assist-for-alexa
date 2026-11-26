"""Dynamic native wakeword devices: authenticated HA API, unlimited devices.

A device is enrolled on explicit app start. Configuration persists in HA storage,
and routed wake events are isolated by installation ID. No microphone audio,
speech transcripts, or credentials are exposed via this API.
"""
import asyncio
import re
import time
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.storage import Store
from .const import DOMAIN

KEY = "wake_devices_dynamic"
DEVICE_ID = re.compile(r"^[a-f0-9]{32}$")
WAKEWORDS = {"Hey Jarvis", "Jarvis", "Alexa"}
CHOICES = {"Hey Jarvis", "Jarvis", "Alexa", "Alle drei"}
DEFAULTS = {"muted": False, "word": "Hey Jarvis",
            "strict": 1, "cooldown": 12, "hold": 50, "followup_limit": 5}
VALID = {"strict": (1, 3), "cooldown": (3, 30), "hold": (10, 90), "followup_limit": (-1, 100)}


class WakeDeviceView(HomeAssistantView):
    url = "/api/tablet_assist_for_alexa/wake_devices"
    name = "api:tablet_assist_for_alexa:wake_devices"
    requires_auth = True

    async def post(self, request):
        hass = request.app[KEY_HASS]
        controller = hass.data.get(DOMAIN, {}).get(KEY)
        if controller is None:
            raise web.HTTPServiceUnavailable()
        user = request.get("hass_user")
        if not user or not user.is_active:
            raise web.HTTPForbidden()
        if request.content_length is None or not 0 < request.content_length <= 4096:
            raise web.HTTPBadRequest()
        try:
            data = await request.json()
            if not isinstance(data, dict):
                raise ValueError("Object expected")
            action = data.get("action")
            identifier = data.get("device_id", "")
            if action != "list" and (not isinstance(identifier, str)
                                     or not DEVICE_ID.fullmatch(identifier)):
                raise ValueError("Invalid device id")
            result = await controller.handle(user, action, identifier, data)
        except PermissionError:
            raise web.HTTPForbidden() from None
        except KeyError:
            raise web.HTTPNotFound() from None
        except ValueError:
            raise web.HTTPBadRequest() from None
        return web.json_response(result, headers={"Cache-Control": "no-store"})


class WakeDevices:
    def __init__(self, hass, store, saved):
        self.hass = hass
        self.store = store
        self.devices = saved
        self.lock = asyncio.Lock()
        self.last_wake = 0.0

    def allowed(self, user, device):
        return user.is_admin or device["user_id"] == user.id

    @staticmethod
    def public(device):
        return {**DEFAULTS, **{k: v for k, v in device.items() if k != "user_id"}}

    async def save(self):
        await self.store.async_save({"devices": self.devices})

    async def handle(self, user, action, identifier, payload):
        async with self.lock:
            if action == "list":
                devices = [self.public(d) for d in self.devices.values()
                           if self.allowed(user, d)]
                return {"devices": sorted(devices, key=lambda d: (d["room"].casefold(), d["device_id"]))}
            if action == "register":
                room = payload.get("room", "")
                if not isinstance(room, str) or len(room) > 48:
                    raise ValueError("Invalid room")
                room = room.strip() or "Jarvis Tablet"
                device = self.devices.get(identifier)
                if device is None:
                    device = dict(DEFAULTS, device_id=identifier, room=room, user_id=user.id)
                    self.devices[identifier] = device
                    await self.save()
                else:
                    if not self.allowed(user, device):
                        raise PermissionError()
                    # The existing friendly name is authoritative. A normal
                    # reconnect must not overwrite a name set in TAFA.
                return {"device": self.public(device)}
            device = self.devices.get(identifier)
            if device is None:
                raise KeyError(identifier)
            if not self.allowed(user, device):
                raise PermissionError()
            if action == "get":
                return {"device": self.public(device)}
            if action == "configure":
                updates = payload.get("settings")
                if not isinstance(updates, dict) or not updates or len(updates) > 6:
                    raise ValueError("Invalid settings")
                cleaned = {}
                for key, value in updates.items():
                    if key == "muted" and type(value) is bool:
                        cleaned[key] = value
                    elif key == "word" and isinstance(value, str) and value in CHOICES:
                        cleaned[key] = value
                    elif key == "room" and isinstance(value, str) and 0 < len(value.strip()) <= 48:
                        cleaned[key] = value.strip()
                    elif key in VALID and type(value) is int and VALID[key][0] <= value <= VALID[key][1]:
                        cleaned[key] = value
                    else:
                        raise ValueError("Invalid setting")
                if cleaned:
                    device.update(cleaned)
                    await self.save()
                return {"device": self.public(device)}
            if action == "delete":
                # Only the administrator can remove an enrolled installation.
                if not user.is_admin:
                    raise PermissionError()
                del self.devices[identifier]
                await self.save()
                return {"removed": True}
            if action == "wake":
                word = payload.get("wakeword")
                stamp = payload.get("timestamp_ms")
                if word not in WAKEWORDS or type(stamp) not in (int, float):
                    raise ValueError("Invalid wake event")
                if abs(time.time() * 1000 - stamp) > 15000:
                    return {"accepted": False, "reason": "stale"}
                selected = device["word"]
                if selected != "Alle drei" and selected != word and not (
                        selected == "Jarvis" and word == "Hey Jarvis"):
                    return {"accepted": False, "reason": "wrong_phrase"}
                if device["muted"]:
                    return {"accepted": False, "reason": "muted"}
                event = {"source": "android_echo_relay", "version": 3,
                         "device_id": identifier, "room": device["room"],
                         "wakeword": word, "timestamp_ms": int(stamp)}
                # All registered device wake candidates are visible for intentional pairing.
                self.hass.bus.async_fire("jarvis_android_wakeword", event)
                now = time.monotonic()
                if now - self.last_wake < 3.0:
                    return {"accepted": False, "reason": "other_device_won"}
                self.last_wake = now
                self.hass.bus.async_fire("jarvis_android_wakeword_routed", event)
                return {"accepted": True}
            raise ValueError("Unknown action")


async def setup_wake_devices(hass, entry):
    data = hass.data.setdefault(DOMAIN, {})
    if data.get(KEY):
        return
    store = Store(hass, 1, DOMAIN + ".wake_devices." + entry.entry_id)
    saved = await store.async_load()
    migrated = False
    if not saved:
        # Import existing, HA-authenticated tablet enrollment without deleting
        # or modifying legacy Jarvis storage. Once saved here, TAFA is owner.
        for legacy in hass.config_entries.async_entries("jarvis_tablet_audio"):
            old = await Store(hass, 1, "jarvis_tablet_audio.wake_devices." + legacy.entry_id).async_load()
            if isinstance(old, dict) and isinstance(old.get("devices"), dict):
                saved = old
                migrated = True
                break
    raw = (saved or {}).get("devices", {})
    devices = {}
    for identifier, device in raw.items():
        if DEVICE_ID.fullmatch(identifier) and isinstance(device, dict):
            if isinstance(device.get("user_id"), str):
                devices[identifier] = {**DEFAULTS, **device}
    if migrated:
        await store.async_save({"devices": devices})
    data[KEY] = WakeDevices(hass, store, devices)
    if not data.get("wake_devices_view_registered"):
        hass.http.register_view(WakeDeviceView())
        data["wake_devices_view_registered"] = True


def unload_wake_devices(hass):
    hass.data.get(DOMAIN, {}).pop(KEY, None)
