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
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import DOMAIN

KEY = "wake_devices_dynamic"
SIGNAL = DOMAIN + "_tablet_changed"
REGISTERED_SIGNAL = DOMAIN + "_tablet_registered"
REMOVED_SIGNAL = DOMAIN + "_tablet_removed"
SETTINGS_SIGNAL = DOMAIN + "_tablet_settings_changed"
DEVICE_ID = re.compile(r"^[a-f0-9]{32}$")
WAKEWORDS = {"Hey Jarvis", "Jarvis", "Alexa"}
CHOICES = {"Hey Jarvis", "Jarvis", "Alexa", "Alle drei"}
DEFAULTS = {"muted": False, "voice_mode": "wake", "word": "Hey Jarvis", "room": "Jarvis Tablet",
            "strict": 1, "cooldown": 12, "hold": 50, "followup_limit": -1,
            "pause_ms": 1700, "mic_gain": 100, "brightness": 80,
            "screen_awake": True, "display_control_enabled": False}
VALID = {"followup_limit": (-1, 100), "strict": (1, 3), "cooldown": (3, 30), "hold": (10, 90),
         "pause_ms": (900, 3200), "mic_gain": (50, 200),
         "brightness": (1, 100)}
TELEMETRY = {"wake_status", "microphone", "audio", "bluetooth", "battery",
             "app_version", "display", "control_channel", "local_followup_limit"}


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
        self.telemetry = {}  # Volatile diagnostics, never persisted.
        self.revisions = {}  # Per-runtime monotonic config revisions.
        self.pending_controls = {}  # Revision and HA monotonic dispatch timestamp.
        self.control_metrics = {}  # Only non-sensitive, volatile ACK diagnostics.

    def allowed(self, user, device):
        return user.is_admin or device["user_id"] == user.id

    def public(self, device):
        identifier = device["device_id"]
        observed = self.telemetry.get(identifier, {})
        seen = observed.get("seen", 0)
        return {**DEFAULTS,
                **{k: v for k, v in device.items() if k != "user_id"},
                "revision": self.revisions.get(identifier, 0),
                "online": bool(seen and time.time() - seen < 45),
                "last_seen": int(seen) if seen else None,
                "telemetry": {k: v for k, v in observed.items() if k != "seen"},
                "control": dict(self.control_metrics.get(identifier, {}))}

    def changed(self, identifier, registered=False):
        async_dispatcher_send(self.hass, SIGNAL, identifier)
        if registered:
            async_dispatcher_send(self.hass, REGISTERED_SIGNAL, identifier)

    def settings_changed(self, identifier):
        """Signal authenticated per-device WS subscribers only for config writes.

        Telemetry and last-seen updates must not create control events.
        The subscription checks device ownership before emitting data.
        """
        revision = self.revisions.get(identifier, 0) + 1
        self.revisions[identifier] = revision
        self.pending_controls[identifier] = (revision, time.monotonic())
        metrics = self.control_metrics.setdefault(identifier, {})
        metrics["revision"] = revision
        metrics["pending"] = True
        metrics["requested_at"] = int(time.time() * 1000)
        async_dispatcher_send(self.hass, SETTINGS_SIGNAL, identifier)

    @staticmethod
    def clean_settings(updates):
        if not isinstance(updates, dict) or not updates or len(updates) > 12:
            raise ValueError("Invalid settings")
        cleaned = {}
        for key, value in updates.items():
            if key in ("muted", "screen_awake", "display_control_enabled") and type(value) is bool:
                cleaned[key] = value
            elif key == "voice_mode" and type(value) is str and value in ("wake", "continuous"):
                cleaned[key] = value
            elif key == "word" and isinstance(value, str) and value in CHOICES:
                cleaned[key] = value
            elif key == "room" and isinstance(value, str) and 0 < len(value.strip()) <= 48:
                cleaned[key] = value.strip()
            elif key in VALID and type(value) is int and VALID[key][0] <= value <= VALID[key][1]:
                cleaned[key] = value
            else:
                raise ValueError("Invalid setting: " + str(key)[:32])
        return cleaned

    async def set_value(self, identifier, key, value):
        """Native HA entity controls and the device API use one validated store."""
        async with self.lock:
            if identifier not in self.devices:
                raise KeyError(identifier)
            changes = self.clean_settings({key: value})
            self.devices[identifier].update(changes)
            await self.save()
            self.changed(identifier)
            self.settings_changed(identifier)

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
                    self.changed(identifier, registered=True)
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
                cleaned = self.clean_settings(payload.get("settings"))
                device.update(cleaned)
                await self.save()
                self.changed(identifier)
                self.settings_changed(identifier)
                return {"device": self.public(device)}
            if action == "delete":
                # Only the administrator can remove an enrolled installation.
                if not user.is_admin:
                    raise PermissionError()
                del self.devices[identifier]
                self.telemetry.pop(identifier, None)
                self.control_metrics.pop(identifier, None)
                self.revisions.pop(identifier, None)
                self.pending_controls.pop(identifier, None)
                await self.save()
                self.changed(identifier)
                async_dispatcher_send(self.hass, REMOVED_SIGNAL, identifier)
                return {"removed": True}
            if action == "ack":
                revision = payload.get("revision")
                channel = payload.get("channel")
                if type(revision) is not int or not 0 <= revision <= 2147483647:
                    raise ValueError("Invalid control revision")
                if channel not in ("websocket", "poll"):
                    raise ValueError("Invalid control channel")
                if revision != self.revisions.get(identifier, 0):
                    return {"accepted": False, "reason": "stale_revision"}
                metrics = self.control_metrics.setdefault(identifier, {})
                pending = self.pending_controls.get(identifier)
                if pending and pending[0] == revision:
                    metrics["latency_ms"] = int(max(0, (time.monotonic() - pending[1]) * 1000))
                    self.pending_controls.pop(identifier, None)
                metrics.update({"channel": channel, "revision": revision,
                                "ack_revision": revision, "pending": False,
                                "applied_at": int(time.time() * 1000)})
                self.changed(identifier)
                return {"accepted": True}
            if action == "report":
                report = payload.get("telemetry")
                if not isinstance(report, dict) or len(report) > 9 or any(
                        k not in TELEMETRY for k in report):
                    raise ValueError("Invalid telemetry")
                sanitized = {}
                for key, value in report.items():
                    if key == "local_followup_limit" and type(value) is int and -1 <= value <= 100:
                        sanitized[key] = value
                    elif key == "battery" and type(value) is int and 0 <= value <= 100:
                        sanitized[key] = value
                    elif isinstance(value, str) and len(value) <= 80:
                        sanitized[key] = value
                    else:
                        raise ValueError("Invalid telemetry value")
                self.telemetry[identifier] = {"seen": time.time(), **sanitized}
                if "control_channel" in sanitized:
                    self.control_metrics.setdefault(identifier, {})["channel"] = sanitized["control_channel"]
                self.changed(identifier)
                return {"accepted": True}
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
                self.telemetry.setdefault(identifier, {})["last_wake"] = int(time.time())
                self.changed(identifier)
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
