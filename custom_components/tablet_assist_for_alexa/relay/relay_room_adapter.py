"""Opt-in HA adapter for room audio; legacy relay is unchanged."""
import asyncio
import re

from aiohttp import web
import voluptuous as vol
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.tts import async_create_stream
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er, device_registry as dr
from homeassistant.util import dt as dt_util
from .const import DOMAIN
from .relay_room_audio import RoomAudioTransport

KEY = "room_audio"
SERVICE = "room_audio"
TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def quiet_now(settings, now):
    start, end = settings.get("quiet_start"), settings.get("quiet_end")
    if not start or not end or start == end:
        return False
    current = now.strftime("%H:%M")
    return start <= current < end if start < end else current >= start or current < end



class RoomAudioView(HomeAssistantView):
    url = "/api/jarvis_echo_relay/room_audio"
    name = "api:jarvis_echo_relay:room_audio"
    requires_auth = True

    async def post(self, request):
        transport = request.app[KEY_HASS].data.get(DOMAIN, {}).get(KEY)
        if transport is None:
            raise web.HTTPServiceUnavailable()
        user = request.get("hass_user")
        if not user or not user.is_active:
            raise web.HTTPForbidden()
        if request.content_length is None or not 0 < request.content_length <= 4096:
            raise web.HTTPBadRequest()
        try:
            data = await request.json()
            if not isinstance(data, dict):
                raise ValueError()
            action = data.get("action")
            principal = user.id
            if action == "connect":
                result = transport.connect(principal)
            elif action == "status":
                result = transport.status(principal, data.get("id"))
                result["device_id"] = transport.settings.get(result["room"], {}).get("device_id", "")
            elif action == "activity":
                transport.activity(principal, data.get("busy"))
                result = {"accepted": True}
            elif action == "submit":
                job = transport.submit(principal, data.get("path"))
                result = {"id": job, "accepted": bool(job)}
            elif action == "poll":
                result = transport.poll(principal, data.get("session"), data.get("ready"))
            elif action == "report":
                result = {"accepted": transport.report(principal, data.get("session"), data.get("id"), data.get("stage"))}
            elif action == "cancel":
                result = {"accepted": transport.cancel(principal, data.get("id"))}
            elif action == "disconnect":
                transport.disconnect(principal, data.get("session"))
                result = {"accepted": True}
            else:
                raise ValueError()
        except PermissionError:
            raise web.HTTPForbidden() from None
        except RuntimeError:
            raise web.HTTPConflict() from None
        except (ValueError, TypeError, KeyError):
            raise web.HTTPBadRequest() from None
        return web.json_response(result, headers={"Cache-Control": "no-store"})


class RoomAudioAdminView(HomeAssistantView):
    """Admin-only pairing for registered Device Bridge tablets.

    The administrator is authenticated by HA. No credentials, microphone
    recordings or room session tokens are returned to the panel.
    """
    url = "/api/jarvis_tablet_audio/room_admin"
    name = "api:jarvis_tablet_audio:room_admin"
    requires_auth = True

    async def post(self, request):
        hass = request.app[KEY_HASS]
        user = request.get("hass_user")
        if not user or not user.is_active or not user.is_admin:
            raise web.HTTPForbidden()
        if request.content_length is None or not 0 < request.content_length <= 4096:
            raise web.HTTPBadRequest()
        try:
            body = await request.json()
            if not isinstance(body, dict) or body.get("action") not in ("list", "pair"):
                raise ValueError("Invalid action")
            data = hass.data.get(DOMAIN, {})
            transport = data.get(KEY)
            controller = data.get("wake_devices_dynamic")
            if transport is None or controller is None:
                raise web.HTTPServiceUnavailable()
            if body["action"] == "list":
                people = [
                    {"id": u.id, "name": u.name}
                    for u in await hass.auth.async_get_users()
                    if u.is_active and not u.is_admin and not u.system_generated
                ]
                paired = [
                    {"room": room, "user_id": principal,
                     "wake_device_id": transport.settings.get(room, {}).get("wake_device_id", ""),
                     **transport.status(principal)}
                    for room, principal in transport.rooms.items()
                ]
                devices = [
                    {"device_id": key, "owner_user_id": value.get("user_id", "")}
                    for key, value in controller.devices.items()
                ]
                return web.json_response({
                    "users": sorted(people, key=lambda p: p["name"].casefold()),
                    "rooms": paired,
                    "devices": devices,
                }, headers={"Cache-Control": "no-store"})

            room = body.get("room")
            principal = body.get("user_id")
            wake_id = body.get("device_id")
            replace = body.get("replace", False)
            if (not isinstance(room, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", room)
                    or not isinstance(principal, str) or not 1 <= len(principal) <= 128
                    or not isinstance(wake_id, str) or not re.fullmatch(r"[a-f0-9]{32}", wake_id)
                    or type(replace) is not bool):
                raise ValueError("Invalid room, user or device")
            target = await hass.auth.async_get_user(principal)
            if not target or not target.is_active or target.is_admin or target.system_generated:
                raise ValueError("Choose an active non-admin Home Assistant user")
            device = controller.devices.get(wake_id)
            if not device:
                raise ValueError("Tablet is no longer registered")
            if device.get("user_id") != principal:
                raise ValueError("Tablet uses another HA account; reconnect it with the selected user's token")
            if any(r != room and p == principal for r, p in transport.rooms.items()):
                raise ValueError("This HA user already has another audio room")
            if any(r != room and s.get("wake_device_id") == wake_id
                   for r, s in transport.settings.items()):
                raise ValueError("This tablet is paired with another audio room")
            current = transport.rooms.get(room)
            if current is not None and current != principal and not replace:
                raise ValueError("Room belongs to another user; confirm reassignment")
            if current != principal:
                transport.provision(room, principal)
            transport.settings[room] = {
                **transport.settings.get(room, {}),
                "wake_device_id": wake_id,
            }
            await data["room_audio_save"]()
            return web.json_response(
                {"room": room, "user_id": principal, "paired": True},
                headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError) as exc:
            return web.json_response({"error": str(exc)[:160]},
                                     status=400, headers={"Cache-Control": "no-store"})


async def setup_room_audio(hass, entry):
    data = hass.data.setdefault(DOMAIN, {})
    transport = RoomAudioTransport()
    store = Store(hass, 1, DOMAIN + ".room_audio." + entry.entry_id)
    saved = await store.async_load()
    for room, principal in (saved or {}).get("rooms", {}).items():
        try:
            transport.provision(room, principal)
        except ValueError:
            continue
    transport.settings = {r: v for r, v in (saved or {}).get("settings", {}).items() if r in transport.rooms and isinstance(v, dict)}
    data[KEY] = transport
    from .relay_room_camera import setup_room_cameras
    cameras = await setup_room_cameras(hass, entry, transport)
    if not data.get("room_audio_view_registered"):
        hass.http.register_view(RoomAudioView())
        data["room_audio_view_registered"] = True
    lock = asyncio.Lock()
    if not data.get("room_admin_view_registered"):
        hass.http.register_view(RoomAudioAdminView())
        data["room_admin_view_registered"] = True

    async def persist():
        await store.async_save({"rooms": transport.rooms.copy(), "settings": transport.settings.copy()})
        cameras.sync()
    data["room_audio_save"] = persist

    def room_settings(values):
        start, end = values.get("quiet_start", ""), values.get("quiet_end", "")
        device = values.get("device_id", "")
        if bool(start) != bool(end) or (start and not (TIME.fullmatch(start) and TIME.fullmatch(end))):
            raise ServiceValidationError("Specify both quiet times as HH:MM, or leave both empty")
        if device and not dr.async_get(hass).async_get(device):
            raise ServiceValidationError("Unknown Home Assistant device ID")
        return {"quiet_start": start, "quiet_end": end, "device_id": device, "camera_enabled": values.get("camera_enabled", False)}

    async def service(call):
        action = call.data["action"]
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if call.context.user_id and (not user or not user.is_admin):
            raise Unauthorized()
        if action in ("provision", "configure", "revoke", "list", "users") and (not user or not user.is_admin):
            raise Unauthorized()
        room = call.data.get("room")
        async with lock:
            if action == "list":
                return {"rooms": [{"room": r, "user_id": p, **transport.status(p), **transport.settings.get(r,{}), "camera_entity_id": cameras.entity_id(r,"camera"), "motion_entity_id": cameras.entity_id(r,"motion"), "camera_online": cameras.store.fresh(r)} for r,p in transport.rooms.items()]}
            if action == "users":
                return {"users": [{"id": u.id, "name": u.name} for u in await hass.auth.async_get_users() if u.is_active and not u.is_admin and not u.system_generated]}
            if action == "provision":
                principal = call.data.get("user_id")
                target = await hass.auth.async_get_user(principal) if principal else None
                if not target or not target.is_active or target.is_admin:
                    raise ServiceValidationError("Use a dedicated active non-admin HA user")
                config = room_settings(call.data)
                try:
                    transport.provision(room, principal)
                except ValueError as error:
                    raise ServiceValidationError(str(error)) from None
                if room in cameras.store.frames:
                    cameras.store.frames[room].clear()
                    cameras.store.frames.pop(room)
                    cameras.store.principals.pop(room, None)
                    cameras.store.intervals.pop(room, None)
                    cameras.store.last_upload.pop(room, None)
                transport.settings[room] = config
                await persist()
                return {"room": room, "configured": True}
            if action == "configure":
                if room not in transport.rooms:
                    raise ServiceValidationError("Unknown room")
                transport.settings[room] = room_settings({**transport.settings.get(room, {}), **call.data})
                await persist()
                return {"room": room, "configured": True}
            if action == "revoke":
                if not isinstance(room, str) or room not in transport.rooms:
                    raise ServiceValidationError("Unknown room")
                transport.revoke(room)
                transport.settings.pop(room,None)
                await persist()
                return {"room": room, "configured": False}
            if action == "announce":
                message = call.data.get("message", "").strip()
                targets = call.data.get("rooms", [room] if room else [])
                if not message or len(message) > 500 or not targets or len(set(targets)) != len(targets) or any(r not in transport.rooms for r in targets):
                    raise ServiceValidationError("Explicit valid rooms and message required")
                engine = er.async_get(hass).async_get_entity_id("tts", "tablet_assist_for_alexa", entry.entry_id + "_stream")
                if not engine:
                    raise ServiceValidationError("Jarvis streaming TTS unavailable")
                results = {}
                for r in targets:
                    if quiet_now(transport.settings.get(r, {}), dt_util.now()):
                        results[r] = {"accepted": False, "status": "quiet_hours"}
                    elif not transport.announcement_ready(r):
                        results[r] = {"accepted": False, "status": "not_ready"}
                    else:
                        stream = async_create_stream(hass, engine, language="de")
                        stream.async_set_message(message)
                        try:
                            job = transport.submit_room(r, stream.url)
                        except ValueError:
                            raise ServiceValidationError("Invalid local TTS stream path") from None
                        results[r] = {"accepted": bool(job), "id": job, "status": "queued" if job else "not_ready"}
                return {"results": results}
        raise ServiceValidationError("Invalid action")

    hass.services.async_register(DOMAIN, SERVICE, service, schema=vol.Schema({
        vol.Required("action"): vol.In(["list", "users", "provision", "configure", "revoke", "announce"]),
        vol.Optional("room"): vol.All(str, vol.Length(max=64)),
        vol.Optional("user_id"): vol.All(str, vol.Length(max=128)),
        vol.Optional("message"): vol.All(str, vol.Length(max=500)),
        vol.Optional("rooms"): vol.All([vol.All(str, vol.Length(max=64))], vol.Length(min=1,max=24)),
        vol.Optional("quiet_start"): vol.All(str,vol.Length(max=5)),
        vol.Optional("quiet_end"): vol.All(str,vol.Length(max=5)),
        vol.Optional("device_id"): vol.All(str,vol.Length(max=64)),
        vol.Optional("camera_enabled"): bool,
    }), supports_response=SupportsResponse.ONLY)


def unload_room_audio(hass):
    from .relay_room_camera import unload_room_cameras
    unload_room_cameras(hass)
    hass.data.get(DOMAIN, {}).pop(KEY, None)
    hass.data.get(DOMAIN, {}).pop("room_audio_save", None)
    if hass.services.has_service(DOMAIN, SERVICE):
        hass.services.async_remove(DOMAIN, SERVICE)
