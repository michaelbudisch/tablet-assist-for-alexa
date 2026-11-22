"""Authenticated tablet image push and read-only local vision actions."""
import asyncio
import io
from datetime import timedelta
from time import monotonic

from aiohttp import web
from PIL import Image, ImageOps
import voluptuous as vol
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers.http import KEY_HASS
from homeassistant.core import SupportsResponse, callback, Context
from homeassistant.exceptions import HomeAssistantError, Unauthorized, ServiceValidationError
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .relay_frames import FrameStore, DEVICE, MAX_IMAGE
from .relay_vision import describe, health, classify, resolve_camera_request

API = "/api/jarvis_echo_relay"

def normalize(data, external=False):
    """Do CPU work off the HA loop. Strip metadata and reject multi-frame/bomb input."""
    if len(data) > (8 * MAX_IMAGE if external else MAX_IMAGE):
        raise ValueError("image size")
    with Image.open(io.BytesIO(data)) as image:
        if image.format not in (("JPEG", "PNG") if external else ("JPEG",)) or image.width * image.height > (12_000_000 if external else 1280 * 960) or getattr(image, "n_frames", 1) != 1:
            raise ValueError("expected bounded JPEG")
        image.load()
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1280, 1280))
        clean = Image.new("RGB", image.size)
        clean.paste(image)
        output = io.BytesIO()
        clean.save(output, "JPEG", quality=85)
        if output.tell() > MAX_IMAGE:
            raise ValueError("image size")
        return output.getvalue()

class RelayRuntime:
    def __init__(self, hass, entry):
        self.hass, self.entry = hass, entry
        self.frames = FrameStore()
        self.listeners = set()
        self.upload_lock = asyncio.Lock()
        self.vision_lock = asyncio.Lock()
        self.last_request = 0

    def notify(self):
        for listener in tuple(self.listeners):
            listener()

    @callback
    def expire(self, _now):
        if self.frames.expire():
            self.notify()

    def is_owner(self, user):
        return bool(user and user.is_admin and (not self.entry.data.get("relay_owner")
                    or self.entry.data["relay_owner"] == user.id))

    def camera_id(self):
        return er.async_get(self.hass).async_get_entity_id("camera", DOMAIN, self.entry.entry_id + "_relay_camera")

def runtime(hass):
    return hass.data.get(DOMAIN, {}).get("relay_camera")

class ResolveCameraView(HomeAssistantView):
    url = API + "/resolve_camera"
    name = "api:jarvis_echo_relay:resolve_camera"
    requires_auth = True

    async def post(self, request):
        relay = runtime(request.app[KEY_HASS])
        if relay is None:
            raise web.HTTPServiceUnavailable()
        if request.content_length is None or not 0 < request.content_length <= 4096:
            raise web.HTTPBadRequest()
        try:
            data = await request.json()
            if not isinstance(data, dict) or set(data) != {"text"} or not isinstance(data["text"], str) or len(data["text"]) > 500:
                raise ValueError()
        except (ValueError, TypeError):
            raise web.HTTPBadRequest() from None
        selected = classify(data["text"])
        if selected is None:
            return web.json_response({"camera_entity_id": None}, headers={"Cache-Control": "no-store"})
        try:
            result = await resolve_camera_request(relay, selected, Context(user_id=request["hass_user"].id))
        except Unauthorized:
            raise web.HTTPForbidden() from None
        except ServiceValidationError:
            raise web.HTTPNotFound() from None
        return web.json_response(result, headers={"Cache-Control": "no-store"})

class RegisterView(HomeAssistantView):
    url = API + "/register"
    name = "api:jarvis_echo_relay:register"
    requires_auth = True
    async def post(self, request):
        relay = runtime(request.app[KEY_HASS])
        if relay is None:
            return web.json_response({"error": "integration unavailable"}, status=503)
        user = request.get("hass_user")
        if not relay.is_owner(user):
            raise web.HTTPForbidden()
        if request.content_length is None or request.content_length > 1024:
            raise web.HTTPRequestEntityTooLarge(max_size=1024, actual_size=request.content_length or 0)
        try:
            data = await request.json()
            device = data["device_id"]
            if set(data) != {"device_id"} or not isinstance(device, str) or not DEVICE.fullmatch(device):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            raise web.HTTPBadRequest() from None
        if relay.entry.data.get("relay_device") not in (None, device):
            return web.json_response({"error": "another tablet is paired"}, status=409)
        relay.hass.config_entries.async_update_entry(relay.entry, data={**relay.entry.data, "relay_owner": user.id, "relay_device": device})
        session = relay.frames.register(device)
        relay.notify()
        return web.json_response({"session": session, "max_age": 15, "max_image": MAX_IMAGE}, headers={"Cache-Control": "no-store"})

class FrameView(HomeAssistantView):
    url = API + "/frame"
    name = "api:jarvis_echo_relay:frame"
    requires_auth = True
    def validate(self, request):
        relay = runtime(request.app[KEY_HASS])
        if relay is None:
            raise web.HTTPServiceUnavailable()
        if not relay.is_owner(request.get("hass_user")):
            raise web.HTTPForbidden()
        if not relay.frames.authorized(request.headers.get("X-Relay-Device"), request.headers.get("X-Relay-Session", "")):
            raise web.HTTPConflict()
        return relay

    async def post(self, request):
        relay = self.validate(request)
        if relay.upload_lock.locked():
            raise web.HTTPTooManyRequests()
        async with relay.upload_lock:
            now = monotonic()
            if now - relay.last_request < 0.5:
                raise web.HTTPTooManyRequests()
            relay.last_request = now
            if request.content_type != "image/jpeg" or request.content_length is None or not 0 < request.content_length <= MAX_IMAGE:
                raise web.HTTPBadRequest()
            try:
                sequence = int(request.headers["X-Relay-Sequence"])
                captured = int(request.headers["X-Relay-Captured-At"])
                flag = request.headers["X-Relay-Motion"]
                if flag not in ("0", "1", "off") or not 0 < captured < 2**53:
                    raise ValueError()
                device, session = request.headers["X-Relay-Device"], request.headers["X-Relay-Session"]
                data = await request.read()
                if len(data) > MAX_IMAGE:
                    raise ValueError()
                jpeg = await relay.hass.async_add_executor_job(normalize, data)
                # Stop/re-pair may have happened while image decoding yielded the event loop.
                relay.frames.put(device, session, sequence, jpeg, captured, None if flag == "off" else flag == "1")
            except PermissionError:
                raise web.HTTPConflict() from None
            except (ValueError, KeyError, TypeError, OSError, Image.DecompressionBombError):
                raise web.HTTPBadRequest() from None
            relay.notify()
            return web.Response(status=204, headers={"Cache-Control": "no-store"})

    async def delete(self, request):
        relay = self.validate(request)
        relay.frames.clear()
        relay.notify()
        return web.Response(status=204)

async def async_setup(hass, entry):
    data = hass.data.setdefault(DOMAIN, {})
    relay = RelayRuntime(hass, entry)
    from .relay_proactive import Proactive
    relay.proactive = Proactive(relay)
    await relay.proactive.setup()
    data["relay_camera"] = relay
    entry.async_on_unload(async_track_time_interval(hass, relay.expire, timedelta(seconds=3)))
    if not data.get("relay_views_registered"):
        hass.http.register_view(RegisterView())
        hass.http.register_view(FrameView())
        hass.http.register_view(ResolveCameraView())
        data["relay_views_registered"] = True

    async def describe_service(call):
        current = runtime(hass)
        if current is None:
            raise ServiceValidationError("Echo Relay unavailable")
        return await describe(current, call.data.get("source", "outside"), call.data.get("mode", "scene"), call.context)

    async def health_service(call):
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if call.context.user_id and (user is None or not user.is_admin):
            raise Unauthorized()
        return await health(runtime(hass))

    async def pipeline_service(call):
        from .relay_pipeline import check_camera_pipeline
        current = runtime(hass)
        if current is None:
            raise ServiceValidationError("Echo Relay unavailable")
        return await check_camera_pipeline(current, call)

    async def models_service(call):
        from .relay_models import model_settings
        current = runtime(hass)
        if current is None:
            raise ServiceValidationError("Echo Relay unavailable")
        return await model_settings(current, call)

    async def unpair(call):
        user = await hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
        if not user or not user.is_admin:
            raise Unauthorized()
        current = runtime(hass)
        current.frames.clear()
        hass.config_entries.async_update_entry(entry, data={key: value for key, value in entry.data.items() if key not in ("relay_owner", "relay_device")})
        current.notify()

    hass.services.async_register(DOMAIN, "describe_camera", describe_service,
        schema=vol.Schema({vol.Optional("source", default="outside"): vol.In(["tablet", "outside", "door"]), vol.Optional("mode", default="scene"): vol.In(["scene", "objects", "object_in_hand"])}), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "camera_vision_status", health_service, schema=vol.Schema({}), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "camera_pipeline_check", pipeline_service,
        schema=vol.Schema({vol.Required("text"): vol.All(str, vol.Length(min=1, max=500)),
            vol.Optional("pipeline_id"): str}), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "model_settings", models_service,
        schema=vol.Schema({vol.Optional("action", default="get"): vol.In(["get", "set"]),
            vol.Optional("text_model"): str, vol.Optional("vision_model"): str,
            vol.Optional("keep_alive"): int, vol.Optional("num_ctx"): int,
            vol.Optional("revision"): vol.All(str, vol.Length(max=64))}), supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "unpair_camera", unpair, schema=vol.Schema({}))
    async def proactive_service(call):
        current = runtime(hass)
        if current is None:
            raise ServiceValidationError("Echo Relay unavailable")
        return await current.proactive.service(call)
    hass.services.async_register(DOMAIN, "proactive", proactive_service, schema=vol.Schema({
        vol.Optional("action", default="get"): vol.In(["get", "set", "check", "heartbeat", "claim", "ack"]),
        vol.Optional("settings"): dict, vol.Optional("revision"): str, vol.Optional("manual", default=False): bool,
        vol.Optional("client_id"): str, vol.Optional("busy", default=True): bool,
        vol.Optional("request_id"): str, vol.Optional("started", default=False): bool}), supports_response=SupportsResponse.ONLY)

def async_unload(hass):
    current = runtime(hass)
    if current:
        current.frames.clear()
        current.notify()
    hass.data.get(DOMAIN, {}).pop("relay_camera", None)
    for service in ("describe_camera", "camera_vision_status", "camera_pipeline_check", "model_settings", "unpair_camera", "proactive"):
        hass.services.async_remove(DOMAIN, service)

async def answer(hass, text, context):
    """Return None for all non-vision requests, preserving existing routing/dialogues."""
    request = classify(text)
    if request is None:
        return None
    relay = runtime(hass)
    if relay is None:
        return "Die Kamerafunktion ist gerade nicht verfügbar."
    try:
        if request[1] == "view":
            await resolve_camera_request(relay, request, context)
            # Visible dashboard clients handle these before Assist/TTS. Native clients
            # receive an honest fallback and never invoke the vision worker.
            return "Die Liveansicht kannst du im Jarvis-Dashboard öffnen."
        result = await describe(relay, *request, context)
        return "Auf dem gerade abgerufenen Einzelbild: " + result["description"]
    except (HomeAssistantError, ValueError, asyncio.TimeoutError):
        return "Das Kamerabild konnte nicht ausgewertet werden. Prüfe Kamera, Bildübertragung und den lokalen Vision-Worker."
