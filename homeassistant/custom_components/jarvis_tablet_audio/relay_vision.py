"""Local single-image vision; fixed camera mapping, authorization, bounded requests and no redirects."""
import asyncio
import base64
import ipaddress
import json
import re
from urllib.parse import urlsplit

import aiohttp
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components.camera import async_get_image
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .const import QWEN_BASE

def classify(text):
    phrase = re.sub(r"[^\wäöüß]+", " ", text.casefold()).strip()
    phrase = re.sub(r"^(?:hey )?jarvis ", "", phrase)
    groups = {
        ("tablet", "object_in_hand"): ("was halte ich in der hand", "was habe ich in der hand", "what am i holding"),
        ("tablet", "scene"): ("was siehst du", "was sieht die tabletkamera", "beschreibe das kamerabild", "what do you see"),
        ("outside", "scene"): ("was ist draußen los", "was ist draussen los", "was siehst du draußen", "was siehst du draussen", "schau nach draußen", "schau nach draussen", "beschreibe die außenkamera", "what is happening outside"),
        ("door", "scene"): ("was sieht die haustürkamera", "was ist vor der haustür zu sehen", "beschreibe die haustürkamera"),
    }
    return next((key for key, values in groups.items() if phrase in values), None)

def worker_url(entry):
    configured = entry.options.get("vision_url", "").strip()
    if not configured:
        parsed = urlsplit(QWEN_BASE)
        configured = f"http://{parsed.hostname}:10503"
    parsed = urlsplit(configured)
    try:
        address = ipaddress.ip_address(parsed.hostname)
        local = (address.is_private or address.is_loopback) and not address.is_unspecified and not address.is_multicast
        port = parsed.port
    except ValueError:
        local, port = False, None
    if parsed.scheme not in ("http", "https") or not local or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/") or port is None:
        raise ServiceValidationError("Vision URL must be an explicit local IP address and port")
    return configured.rstrip("/")

async def request(relay, path, payload=None):
    token = relay.entry.data.get("qwen_token", "")
    if len(token) < 32:
        raise ServiceValidationError("Worker token is missing")
    client = async_get_clientsession(relay.hass)
    try:
        async with client.request("POST" if payload is not None else "GET", worker_url(relay.entry) + path,
                headers={"X-API-Key": token}, json=payload, allow_redirects=False,
                timeout=aiohttp.ClientTimeout(total=110 if payload else 10)) as response:
            if response.status != 200:
                raise ServiceValidationError("Local vision worker unavailable")
            data = bytearray()
            async for block in response.content.iter_chunked(8192):
                data.extend(block)
                if len(data) > 65536:
                    raise ServiceValidationError("Vision reply too large")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise ValueError()
            return result
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
        raise ServiceValidationError("Local vision request failed") from error

async def health(relay):
    result = await request(relay, "/health")
    return {"ready": result.get("ready") is True, "model": str(result.get("model", ""))[:100], "busy": result.get("busy") is True,
            "tablet_available": relay.frames.fresh, "outside_camera": relay.entry.options.get("vision_outside_camera", ""),
            "door_camera": relay.entry.options.get("vision_door_camera", "")}

async def describe(relay, source, mode, context):
    if relay.vision_lock.locked():
        raise ServiceValidationError("Vision is already busy")
    async with relay.vision_lock:
        entity_id = relay.camera_id() if source == "tablet" else relay.entry.options.get("vision_outside_camera" if source == "outside" else "vision_door_camera", "")
        if not entity_id or not re.fullmatch(r"camera\.[a-z0-9_]+", entity_id):
            raise ServiceValidationError("Select this camera in Jarvis integration options")
        if context.user_id:
            user = await relay.hass.auth.async_get_user(context.user_id)
            if user is None or not user.permissions.check_entity(entity_id, POLICY_READ):
                raise Unauthorized()
        if source == "tablet":
            if not relay.frames.fresh:
                raise ServiceValidationError("Tablet camera has no fresh image")
            image = relay.frames.image
            captured_at = relay.frames.captured_at
        else:
            state = relay.hass.states.get(entity_id)
            if state is None or state.state in ("unknown", "unavailable"):
                raise ServiceValidationError("Camera unavailable")
            async with asyncio.timeout(15):
                picture = await async_get_image(relay.hass, entity_id, timeout=12)
            image = picture.content
            # Normalize external camera images off-loop and bound the worker input.
            from .relay_camera import normalize
            image = await relay.hass.async_add_executor_job(normalize, image, True)
            captured_at = None
        if len(image) > 2 * 1024 * 1024:
            raise ServiceValidationError("Image too large")
        result = await request(relay, "/describe", {"image": base64.b64encode(image).decode("ascii"), "mode": mode})
        description = result.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ServiceValidationError("Empty vision reply")
        return {"description": description.strip()[:700], "camera_entity_id": entity_id, "captured_at": captured_at,
                "model": str(result.get("model", ""))[:100], "limitation": "single image; may be inaccurate"}
