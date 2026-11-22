"""Synthetic fixtures only. Never install on a real Home Assistant instance."""
import asyncio
import base64
from datetime import timedelta
import io
import json
from pathlib import Path
import traceback

from aiohttp import web, ClientSession
from PIL import Image, ImageDraw
from homeassistant.core import Context
from homeassistant.components import camera, conversation
from homeassistant.helpers import entity_registry as er
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

CHECKS = []
def check(value, label):
    if not value:
        raise AssertionError(label)
    CHECKS.append(label)

async def wait_for(predicate):
    async with asyncio.timeout(30):
        while not predicate():
            await asyncio.sleep(0.1)

async def run(hass):
    from custom_components.jarvis_tablet_audio.relay_camera import runtime
    from custom_components.jarvis_tablet_audio.relay_frames import FrameStore
    from custom_components.jarvis_tablet_audio.relay_vision import classify
    clock = [1.0]
    frames = FrameStore(lambda: clock[0])
    device = "a" * 32
    nonce = frames.register(device)
    frames.put(device, nonce, 1, b"fixture", 1, True)
    check(frames.fresh, "fresh frame accepted")
    clock[0] = 17
    check(not frames.fresh and frames.expire() and frames.image is None, "stale image discarded")
    for phrase in ("Wie wird das Wetter draußen?", "Schalte das Licht an", "Was ist ein Kameraobjektiv?"):
        check(classify(phrase) is None, "ordinary request preserved: " + phrase)
    check(classify("Was ist draußen los?") == ("outside", "scene"), "outdoor sight question routed")

    image = Image.new("RGB", (640, 480), "white")
    ImageDraw.Draw(image).rectangle((80, 80, 300, 300), fill="red")
    binary = io.BytesIO(); image.save(binary, "JPEG"); jpeg = binary.getvalue()
    seen = []
    worker = web.Application()
    async def health(request):
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3, "worker authentication")
        return web.json_response({"ready": True, "model": "synthetic-ci", "busy": False})
    async def describe(request):
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3, "vision authenticated")
        data = await request.json()
        check(set(data) == {"image", "mode"}, "no arbitrary prompt or URL forwarded")
        with Image.open(io.BytesIO(base64.b64decode(data["image"]))) as img:
            check(img.width <= 1280 and img.height <= 1280, "vision image bounded")
        seen.append(data["mode"])
        return web.json_response({"description": "Ein rotes Rechteck auf hellem Hintergrund.", "model": "synthetic-ci"})
    worker.router.add_get("/health", health); worker.router.add_post("/describe", describe)
    runner = web.AppRunner(worker); await runner.setup(); await web.TCPSite(runner, "127.0.0.1", 15003).start()
    try:
        flow = await hass.config_entries.flow.async_init("jarvis_tablet_audio", context={"source": "user"})
        created = await hass.config_entries.flow.async_configure(flow["flow_id"], {"qwen_token": "test-worker-token-" * 3})
        check(created["type"] == "create_entry", "Jarvis config entry created")
        entry = created["result"]
        await wait_for(lambda: runtime(hass) is not None and runtime(hass).camera_id())
        relay = runtime(hass)
        cid = relay.camera_id()
        registry = er.async_get(hass)
        agent = registry.async_get_entity_id("conversation", "jarvis_tablet_audio", entry.entry_id + "_conversation_router")
        check(hass.states.get(cid).state == "unavailable", "camera initially unavailable")
        admin = await hass.auth.async_create_user("Camera fixture", group_ids=["system-admin"])
        guest = await hass.auth.async_create_user("Guest fixture", group_ids=["system-users"])
        refresh = await hass.auth.async_create_refresh_token(admin, client_id="https://camera-fixture.invalid")
        bearer = hass.auth.async_create_access_token(refresh)
        refresh2 = await hass.auth.async_create_refresh_token(guest, client_id="https://camera-fixture.invalid")
        guest_bearer = hass.auth.async_create_access_token(refresh2)
        base = "http://127.0.0.1:8123/api/jarvis_echo_relay"
        async with ClientSession() as client:
            async with client.post(base + "/register", json={"device_id": device}) as response:
                check(response.status == 401, "anonymous upload rejected")
            async with client.post(base + "/register", json={"device_id": device}, headers={"Authorization": "Bearer " + guest_bearer}) as response:
                check(response.status == 403, "non-admin pairing rejected")
            auth = {"Authorization": "Bearer " + bearer}
            async with client.post(base + "/register", json={"device_id": device}, headers=auth) as response:
                check(response.status == 200, "tablet paired through real HTTP")
                nonce = (await response.json())["session"]
            headers = {**auth, "Content-Type": "image/jpeg", "X-Relay-Device": device, "X-Relay-Session": nonce,
                       "X-Relay-Sequence": "1", "X-Relay-Captured-At": "1795390000000", "X-Relay-Motion": "1"}
            async with client.post(base + "/frame", headers=headers, data=jpeg) as response:
                check(response.status == 204, "JPEG delivered over authenticated HTTP")
            check(hass.states.get(cid).state != "unavailable", "camera available after push")
            read = await camera.async_get_image(hass, cid)
            check(read.content.startswith(b"\xff\xd8"), "HA camera returns real JPEG")
            motion = registry.async_get_entity_id("binary_sensor", "jarvis_tablet_audio", entry.entry_id + "_relay_motion")
            check(hass.states.is_state(motion, "on"), "motion sensor updated")
            async with client.post(base + "/register", json={"device_id": "b" * 32}, headers=auth) as response:
                check(response.status == 409, "different tablet cannot replace pairing")
            options = await hass.config_entries.options.async_init(entry.entry_id)
            check(options["type"] == "form", "camera options form loads")
            saved = await hass.config_entries.options.async_configure(options["flow_id"], {"vision_url": "http://127.0.0.1:15003", "vision_outside_camera": cid, "vision_door_camera": cid})
            check(saved["type"] == "create_entry", "camera options validated")
            old = relay
            await wait_for(lambda: runtime(hass) is not None and runtime(hass) is not old and runtime(hass).camera_id())
            relay = runtime(hass)
            async with client.post(base + "/frame", headers=headers, data=jpeg) as response:
                check(response.status == 409, "reload invalidates old session")
            async with client.post(base + "/register", json={"device_id": device}, headers=auth) as response:
                nonce = (await response.json())["session"]
            headers["X-Relay-Session"] = nonce
            async with client.post(base + "/frame", headers=headers, data=jpeg) as response:
                check(response.status == 204, "paired tablet reconnects after reload")
            status = await hass.services.async_call("jarvis_tablet_audio", "camera_vision_status", {}, blocking=True, return_response=True, context=Context(user_id=admin.id))
            check(status["ready"] is True, "health uses existing worker token")
            result = await hass.services.async_call("jarvis_tablet_audio", "describe_camera", {"source": "tablet"}, blocking=True, return_response=True, context=Context(user_id=admin.id))
            check("Rechteck" in result["description"], "service describes tablet image")
            reply = await conversation.async_converse(hass, text="Was ist draußen los?", conversation_id=None, agent_id=agent, language="de", context=Context(user_id=admin.id))
            check("Rechteck" in reply.response.as_dict()["speech"]["plain"]["speech"], "spoken question returns vision response")
            async with client.delete(base + "/frame", headers=headers) as response:
                check(response.status == 204, "stop clears image")
            check(hass.states.get(cid).state == "unavailable" and relay.frames.image is None, "no stale fallback after stop")
            async with client.post(base + "/frame", headers={**headers, "X-Relay-Sequence": "2"}, data=jpeg) as response:
                check(response.status == 409, "late frame after stop rejected")
        check(len(seen) == 2, "vision called only for explicit service/question")
    finally:
        await runner.cleanup()

async def async_setup(hass, config):
    async def execute(_event):
        result = {"ok": False}
        try:
            await run(hass)
            result = {"ok": True, "checks": CHECKS}
        except Exception:
            result["error"] = traceback.format_exc()
        await hass.async_add_executor_job(Path("/config/result.json").write_text, json.dumps(result, ensure_ascii=False))
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, execute)
    return True
