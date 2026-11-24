"""Opt-in HA adapter for room audio; legacy relay is unchanged."""
import asyncio

from aiohttp import web
import voluptuous as vol
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.tts import async_create_stream
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN
from .relay_room_audio import RoomAudioTransport

KEY = "room_audio"
SERVICE = "room_audio"


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
    data[KEY] = transport
    if not data.get("room_audio_view_registered"):
        hass.http.register_view(RoomAudioView())
        data["room_audio_view_registered"] = True
    lock = asyncio.Lock()

    async def service(call):
        action = call.data["action"]
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if call.context.user_id and (not user or not user.is_admin):
            raise Unauthorized()
        if action in ("provision", "revoke", "list") and (not user or not user.is_admin):
            raise Unauthorized()
        room = call.data.get("room")
        async with lock:
            if action == "list":
                return {"rooms": [{"room": r, "user_id": p, **transport.status(p)} for r,p in transport.rooms.items()]}
            if action == "provision":
                principal = call.data.get("user_id")
                target = await hass.auth.async_get_user(principal) if principal else None
                if not target or not target.is_active or target.is_admin:
                    raise ServiceValidationError("Use a dedicated active non-admin HA user")
                try:
                    transport.provision(room, principal)
                except ValueError as error:
                    raise ServiceValidationError(str(error)) from None
                await store.async_save({"rooms": transport.rooms.copy()})
                return {"room": room, "configured": True}
            if action == "revoke":
                if not isinstance(room, str) or room not in transport.rooms:
                    raise ServiceValidationError("Unknown room")
                transport.revoke(room)
                await store.async_save({"rooms": transport.rooms.copy()})
                return {"room": room, "configured": False}
            if action == "announce":
                message = call.data.get("message", "").strip()
                if not message or len(message) > 500 or room not in transport.rooms:
                    raise ServiceValidationError("Room and message required")
                if not transport.status(transport.rooms[room])["ready"]:
                    return {"accepted": False, "status": "not_ready"}
                engine = er.async_get(hass).async_get_entity_id("tts", DOMAIN, entry.entry_id + "_stream")
                if not engine:
                    raise ServiceValidationError("Jarvis streaming TTS unavailable")
                stream = async_create_stream(hass, engine, language="de")
                stream.async_set_message(message)
                try:
                    job = transport.submit_room(room, stream.url)
                except ValueError:
                    raise ServiceValidationError("Invalid local TTS stream path") from None
                return {"accepted": bool(job), "id": job, "status": "queued" if job else "not_ready"}
        raise ServiceValidationError("Invalid action")

    hass.services.async_register(DOMAIN, SERVICE, service, schema=vol.Schema({
        vol.Required("action"): vol.In(["list", "provision", "revoke", "announce"]),
        vol.Optional("room"): vol.All(str, vol.Length(max=64)),
        vol.Optional("user_id"): vol.All(str, vol.Length(max=128)),
        vol.Optional("message"): vol.All(str, vol.Length(max=500)),
    }), supports_response=SupportsResponse.ONLY)


def unload_room_audio(hass):
    hass.data.get(DOMAIN, {}).pop(KEY, None)
    if hass.services.has_service(DOMAIN, SERVICE):
        hass.services.async_remove(DOMAIN, SERVICE)
