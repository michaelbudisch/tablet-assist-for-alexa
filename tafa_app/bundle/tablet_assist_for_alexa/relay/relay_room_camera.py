"""Authenticated opt-in shared-room camera receiver and HA entity registration."""
import asyncio
from datetime import timedelta
from time import monotonic
from aiohttp import web
from PIL import Image
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.http import KEY_HASS
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.core import callback
from .const import DOMAIN
from .relay_frames import MAX_IMAGE
from .relay_room_camera_store import RoomCameraStore

KEY = "room_cameras"
API = "/api/jarvis_echo_relay/room_camera"


class RoomCameraHub:
    def __init__(self, hass, entry, transport):
        self.hass, self.entry = hass, entry
        self.store = RoomCameraStore(transport, monotonic)
        self.transport = transport
        self.listeners = {}
        self.adders = {}
        self.known = {}
        self.decode = asyncio.Semaphore(2)

    def uid(self, room, kind):
        return self.entry.entry_id + "_room_" + room + "_" + kind

    def device_info(self, room):
        return DeviceInfo(identifiers={(DOMAIN, self.entry.entry_id + "_room_" + room)},
                          name="Jarvis Tablet " + room, manufacturer="Jarvis", model="Echo Relay")

    def entity_id(self, room, kind):
        domain = "camera" if kind == "camera" else "binary_sensor"
        return er.async_get(self.hass).async_get_entity_id(domain, "tablet_assist_for_alexa", self.uid(room, kind))

    @callback
    def attach(self, kind, add_entities, factory):
        self.adders[kind] = (add_entities, factory)
        self.known[kind] = set()
        self.sync()

    @callback
    def notify(self, room):
        for listener in tuple(self.listeners.get(room, ())):
            listener()

    @callback
    def sync(self):
        changed = self.store.sync()
        for kind, (add, factory) in self.adders.items():
            rooms = set(self.transport.rooms) - self.known[kind]
            if rooms:
                self.known[kind].update(rooms)
                add([factory(self, room) for room in sorted(rooms)])
        for room in set(self.transport.rooms) | changed | set(self.listeners):
            self.notify(room)

    @callback
    def expire(self, _now):
        for room in self.store.expire():
            self.notify(room)


def hub(hass):
    return hass.data.get(DOMAIN, {}).get(KEY)


def get_hub(request):
    current = hub(request.app[KEY_HASS])
    if current is None:
        raise web.HTTPServiceUnavailable()
    user = request.get("hass_user")
    if not user or not user.is_active:
        raise web.HTTPForbidden()
    return current, user.id


class RoomCameraRegister(HomeAssistantView):
    url = API + "/register"
    name = "api:jarvis_echo_relay:room_camera_register"
    requires_auth = True

    async def post(self, request):
        current, principal = get_hub(request)
        if request.content_length is None or not 0 < request.content_length <= 1024:
            raise web.HTTPBadRequest()
        try:
            data = await request.json()
            if not isinstance(data, dict) or set(data) != {"device_id"}:
                raise ValueError()
            room, session = current.store.register(principal, data["device_id"])
        except PermissionError:
            raise web.HTTPForbidden() from None
        except RuntimeError:
            raise web.HTTPConflict() from None
        except (ValueError, TypeError):
            raise web.HTTPBadRequest() from None
        current.notify(room)
        return web.json_response({"session": session, "max_age": 15, "max_image": MAX_IMAGE},
                                 headers={"Cache-Control": "no-store"})


class RoomCameraFrame(HomeAssistantView):
    url = API + "/frame"
    name = "api:jarvis_echo_relay:room_camera_frame"
    requires_auth = True

    async def post(self, request):
        current, principal = get_hub(request)
        device, session = request.headers.get("X-Relay-Device"), request.headers.get("X-Relay-Session")
        try:
            room = current.store.room_for(principal)
        except PermissionError:
            raise web.HTTPForbidden() from None
        try:
            current.store.authorized(principal, device, session)
        except PermissionError:
            raise web.HTTPConflict() from None
        if request.content_type != "image/jpeg" or request.content_length is None or not 0 < request.content_length <= MAX_IMAGE:
            raise web.HTTPBadRequest()
        if current.decode.locked():
            raise web.HTTPTooManyRequests()
        try:
            seq = int(request.headers["X-Relay-Sequence"])
            captured = int(request.headers["X-Relay-Captured-At"])
            interval = int(request.headers.get("X-Relay-Interval", "2"))
            flag = request.headers["X-Relay-Motion"]
            if flag not in ("0", "1", "off") or not 0 < captured < 2**53:
                raise ValueError()
            async with current.decode:
                from .relay_camera import normalize
                jpeg = await current.hass.async_add_executor_job(normalize, await request.read())
                room = current.store.put(principal, device, session, seq, jpeg, captured,
                                         None if flag == "off" else flag == "1", interval)
        except PermissionError:
            raise web.HTTPConflict() from None
        except RuntimeError:
            raise web.HTTPTooManyRequests() from None
        except (ValueError, TypeError, KeyError, OSError, Image.DecompressionBombError):
            raise web.HTTPBadRequest() from None
        current.notify(room)
        return web.Response(status=204, headers={"Cache-Control": "no-store"})

    async def delete(self, request):
        current, principal = get_hub(request)
        try:
            room = current.store.stop(principal, request.headers.get("X-Relay-Device"),
                                      request.headers.get("X-Relay-Session"))
        except PermissionError:
            raise web.HTTPConflict() from None
        current.notify(room)
        return web.Response(status=204, headers={"Cache-Control": "no-store"})


async def setup_room_cameras(hass, entry, transport):
    data = hass.data.setdefault(DOMAIN, {})
    current = RoomCameraHub(hass, entry, transport)
    data[KEY] = current
    if not data.get("room_camera_views_registered"):
        hass.http.register_view(RoomCameraRegister())
        hass.http.register_view(RoomCameraFrame())
        data["room_camera_views_registered"] = True
    entry.async_on_unload(async_track_time_interval(hass, current.expire, timedelta(seconds=2)))
    return current


def unload_room_cameras(hass):
    current = hass.data.get(DOMAIN, {}).pop(KEY, None)
    if current:
        for frames in current.store.frames.values():
            frames.clear()
        current.listeners.clear()
        current.adders.clear()
