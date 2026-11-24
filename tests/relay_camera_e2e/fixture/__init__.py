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
from homeassistant.exceptions import Unauthorized, ServiceValidationError
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
    from custom_components.jarvis_tablet_audio.relay_pipeline import run_intent
    from homeassistant.components.assist_pipeline.models import Pipeline
    from homeassistant.setup import async_setup_component
    await async_setup_component(hass, "assist_pipeline", {})
    clock = [1.0]
    frames = FrameStore(lambda: clock[0])
    device = "a" * 32
    nonce = frames.register(device)
    frames.put(device, nonce, 1, b"fixture", 1, True)
    check(frames.fresh, "fresh frame accepted")
    clock[0] = 17
    check(not frames.fresh and frames.expire() and frames.image is None, "stale image discarded")
    for phrase in ("Wie wird das Wetter draußen?", "Schalte das Licht an", "Was ist ein Kameraobjektiv?", "Öffne die Haustür", "Ist die Haustür abgeschlossen?", "Wer wartet auf den Bus?", "Schalte die Vorderkamera aus", "Ist die Vorderkamera an?", "Wie funktioniert die Vorderkamera?"):
        check(classify(phrase) is None, "ordinary request preserved: " + phrase)
    check(classify("Was ist draußen los?") == ("outside", "scene"), "outdoor sight question routed")
    for phrase in ("Was siehst du in der Vorderkamera?", "Was siehst du an der Vorderseite?", "Was zeigt die Vorderkamera?", "Was ist an der Vorderseite los?", "Was siehst du vorne?"):
        check(classify(phrase) == ("outside", "scene"), "outdoor camera alias: " + phrase)
    for phrase in ("Wer ist an der Haustür?", "Was ist an der Haustür?", "Was siehst du an der Haustür?", "Was siehst du in der Haustürkamera?", "Was ist auf der Haustür Kamera zu sehen?", "Was erkennst du vor der Tür?", "Wer steht gerade vor der Tür?", "Was ist vor meiner Haustür los?", "Hey Jarvis, kannst du mir bitte sagen, wer ist an der Haustuer?", "Who is at the front door?"):
        check(classify(phrase) == ("door", "scene"), "door sight variant: " + phrase)
    view_phrases = {
        "door": ("Zeige Haustür Kamera", "Zeige Haustürkamera", "Zeige Haustür", "Haustür", "Haustürkamera", "Haustür Kamera", "Kamera Haustür", "Klingel", "Zeige Klingel", "Klingelkamera", "Kannst du mir bitte zeigen die Haustürkamera"),
        "outside": ("Zeige Vorderseite", "Vorderseite", "Vorderseitenkamera", "Vorderseite Kamera", "Kamera Vorderseite", "Vorderkamera", "Zeig mir die Außenkamera", "Schau nach draußen"),
        "all": ("Zeige Kameras", "Zeig mir alle Kameras", "Kameras"),
    }
    for source, phrases in view_phrases.items():
        for phrase in phrases:
            check(classify(phrase) == (source, "view"), "view-only alias: " + phrase)
    for phrase in ("Zeige nicht die Haustür", "Was ist eine Haustürkamera?", "Warum ist die Klingel kaputt?", "Klingel ausschalten"):
        check(classify(phrase) is None, "non-visual request preserved: " + phrase)

    image = Image.new("RGB", (640, 480), "white")
    ImageDraw.Draw(image).rectangle((80, 80, 300, 300), fill="red")
    binary = io.BytesIO(); image.save(binary, "JPEG"); jpeg = binary.getvalue()
    seen = []
    vision_payloads = []
    worker = web.Application()
    worker_state = {"busy":False,"uncertain":False,"offline":False}
    async def health(request):
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3, "worker authentication")
        return web.json_response({"ready": True, "model": "synthetic-ci", "busy": False})
    async def describe(request):
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3, "vision authenticated")
        data = await request.json()
        check(set(data) == {"image", "mode", "model", "keep_alive", "num_ctx"}, "no arbitrary prompt or URL forwarded")
        vision_payloads.append(data)
        with Image.open(io.BytesIO(base64.b64decode(data["image"]))) as img:
            check(img.width <= 1280 and img.height <= 1280, "vision image bounded")
        seen.append(data["mode"])
        return web.json_response({"description": "Ein rotes Rechteck auf hellem Hintergrund.", "model": "synthetic-ci"})
    worker.router.add_get("/health", health); worker.router.add_post("/describe", describe)
    async def model_runtime(request):
        if worker_state["offline"]:
            return web.json_response({"error":"offline"},status=503)
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3, "model runtime authentication")
        return web.json_response({"settings_api":1,"detection_api":1,"text_models":["qwen3:4b-instruct","qwen3-vl:4b-instruct"],
            "vision_models":["qwen3-vl:4b-instruct"],"loaded":[],"busy":worker_state["busy"]})
    worker.router.add_get("/runtime", model_runtime)
    async def detect(request):
        check(request.headers.get("X-API-Key") == "test-worker-token-" * 3,"detection authenticated")
        return web.json_response({"detection_api":1,"detection":{"person_count":1,"dog_count":0,"age_groups":["adult"],"uncertain":worker_state["uncertain"]}})
    worker.router.add_post("/detect", detect)
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
        restricted = await hass.auth.async_create_user("No camera access fixture", group_ids=[])
        refresh = await hass.auth.async_create_refresh_token(admin, client_id="https://camera-fixture.invalid")
        bearer = hass.auth.async_create_access_token(refresh)
        refresh2 = await hass.auth.async_create_refresh_token(guest, client_id="https://camera-fixture.invalid")
        guest_bearer = hass.auth.async_create_access_token(refresh2)
        restricted_refresh = await hass.auth.async_create_refresh_token(restricted, client_id="https://camera-fixture.invalid")
        restricted_bearer = hass.auth.async_create_access_token(restricted_refresh)
        base = "http://127.0.0.1:8123/api/jarvis_echo_relay"
        async with ClientSession() as client:
            from .room_audio import check_room_audio
            await check_room_audio(hass, client, base, admin, guest, guest_bearer, check)
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
            async with client.post(base + "/resolve_camera", json={"text": "Wer ist an der Haustür?"}) as response:
                check(response.status == 401, "preview resolution requires authentication")
            async with client.post(base + "/resolve_camera", json={"text": "Wer ist an der Haustür?"}, headers=auth) as response:
                resolved = await response.json()
                check(response.status == 200 and resolved["camera_entity_id"] == cid and resolved["source"] == "door" and resolved["action"] == "describe", "requesting UI resolves configured door camera")
            for phrase in ("Zeige Haustürkamera", "Kamera Haustür", "Klingel", "Zeige Vorderseite", "Zeige Kameras"):
                async with client.post(base + "/resolve_camera", json={"text": phrase}, headers=auth) as response:
                    resolved = await response.json()
                    check(response.status == 200 and resolved["camera_entity_ids"] == [cid] and resolved["action"] == "view", "view resolution without inference: " + phrase)
            async with client.post(base + "/resolve_camera", json={"text": "Ist die Haustür abgeschlossen?"}, headers=auth) as response:
                check((await response.json())["camera_entity_id"] is None, "door control query has no camera popup")
            async with client.post(base + "/resolve_camera", json={"text": "Wer ist an der Haustür?"}, headers={"Authorization": "Bearer " + restricted_bearer}) as response:
                check(response.status == 403, "preview obeys entity read permissions")
            async with client.post(base + "/resolve_camera", json={"text": "Zeige Kameras"}, headers={"Authorization": "Bearer " + restricted_bearer}) as response:
                check(response.status == 403, "overview does not expose unauthorized camera IDs")
            check(not seen, "preview resolution does not invoke model")
            result = await hass.services.async_call("jarvis_tablet_audio", "describe_camera", {"source": "tablet"}, blocking=True, return_response=True, context=Context(user_id=admin.id))
            check("Rechteck" in result["description"], "service describes tablet image")
            reply = await conversation.async_converse(hass, text="Wer ist an der Haustür?", conversation_id=None, agent_id=agent, language="de", context=Context(user_id=admin.id))
            check("Rechteck" in reply.response.as_dict()["speech"]["plain"]["speech"], "spoken question returns vision response")
            pipeline = Pipeline(conversation_engine=agent, conversation_language="de", language="de", name="Camera routing fixture",
                stt_engine=None, stt_language=None, tts_engine=None, tts_language=None, tts_voice=None,
                wake_word_entity=None, wake_word_id=None, prefer_local_intents=False)
            for phrase in ("Wer ist an der Tür?", "Wer ist an der Haustür?", "Was siehst du an der Haustür?", "Was siehst du in der Haustürkamera?", "Was siehst du in der Vorderkamera?", "Was siehst du an der Vorderseite?"):
                result = await run_intent(hass, pipeline, Context(user_id=admin.id), phrase)
                check(not result["errors"] and "Rechteck" in result["speech"] and result["processed_locally"] is False,
                    "full Assist pipeline reaches vision: " + phrase)
            count_before_views = len(seen)
            for phrase in ("Zeige Haustürkamera", "Haustür", "Kamera Haustür", "Klingel", "Zeige Vorderseite", "Zeige Kameras"):
                result = await run_intent(hass, pipeline, Context(user_id=admin.id), phrase)
                check(not result["errors"] and "Liveansicht" in result["speech"] and len(seen) == count_before_views,
                    "view-only native fallback never invokes vision: " + phrase)
            # No real devices: this synthetic service records native HA command execution.
            lamp = registry.async_get_or_create("light", "relay_camera_ci", "routing-fixture", suggested_object_id="routing_fixture", original_name="Testlampe")
            hass.states.async_set(lamp.entity_id, "off", {"friendly_name": "Testlampe", "supported_features": 0})
            async def turn_on(call):
                hass.states.async_set(lamp.entity_id, "on", {"friendly_name": "Testlampe", "supported_features": 0})
            hass.services.async_register("light", "turn_on", turn_on)
            result = await run_intent(hass, pipeline, Context(user_id=admin.id), "Schalte die Testlampe ein")
            check(not result["errors"] and hass.states.is_state(lamp.entity_id, "on"), "native HA control preserved after Jarvis routing")
            from custom_components.jarvis_tablet_audio.relay_routing import native_reply
            from types import SimpleNamespace
            unknown = SimpleNamespace(text="Erkläre Quantenverschränkung", context=Context(user_id=admin.id), language="de", device_id=None, satellite_id=None)
            check(await native_reply(hass, unknown) is None, "unmatched native request remains eligible for LLM")
            try:
                await hass.services.async_call("jarvis_tablet_audio", "camera_pipeline_check", {"text": "Wer ist an der Haustür?"}, blocking=True, return_response=True, context=Context(user_id=guest.id))
            except Unauthorized:
                check(True, "camera pipeline diagnostic requires administrator")
            else:
                raise AssertionError("Non-admin pipeline diagnostic accepted")
            try:
                await hass.services.async_call("jarvis_tablet_audio", "camera_pipeline_check", {"text": "Schalte die Testlampe ein"}, blocking=True, return_response=True, context=Context(user_id=admin.id))
            except ServiceValidationError:
                check(True, "camera diagnostic rejects device commands")
            else:
                raise AssertionError("Diagnostic accepted device control")
            # Native config-entry/subentry persistence, with no real Ollama process or credentials.
            from homeassistant.config_entries import ConfigEntry, ConfigEntryDisabler
            from types import MappingProxyType
            from custom_components.jarvis_tablet_audio import conversation as jarvis_router
            model_entry = ConfigEntry(version=3,minor_version=3,domain="ollama",title="Model settings fixture",
                data={"url":"http://127.0.0.1:15003"},options={},source="user",unique_id=None,
                disabled_by=ConfigEntryDisabler.USER,discovery_keys=MappingProxyType({}),subentries_data=[{"subentry_type":"conversation","title":"Fixture KI",
                    "unique_id":None,"data":{"model":"qwen3:4b-instruct","keep_alive":120,"num_ctx":4096,
                        "prompt":"fixture prompt kept","max_history":6,"think":False}}])
            await hass.config_entries.async_add(model_entry)
            subentry=next(iter(model_entry.subentries.values()))
            model_agent=registry.async_get_or_create("conversation","ollama",subentry.subentry_id,
                config_entry=model_entry,config_subentry_id=subentry.subentry_id,suggested_object_id="fixture_ki")
            jarvis_router.LLM_AGENT=model_agent.entity_id
            async def models(data, user=admin):
                return await hass.services.async_call("jarvis_tablet_audio","model_settings",data,
                    blocking=True,return_response=True,context=Context(user_id=user.id))
            try:
                await models({"action":"get"},guest)
            except Unauthorized:
                check(True,"model settings require administrator")
            else:
                raise AssertionError("Guest model settings accepted")
            before=await models({"action":"get"})
            saved=await models({"action":"set","revision":before["revision"],"text_model":"qwen3-vl:4b-instruct",
                "vision_model":"qwen3-vl:4b-instruct","keep_alive":300,"num_ctx":2048})
            await hass.async_block_till_done()
            check(saved["saved"] and saved["shared"] and subentry.data["model"]=="qwen3-vl:4b-instruct", "shared model persisted in native Ollama subentry")
            check(subentry.data["prompt"]=="fixture prompt kept" and subentry.data["max_history"]==6 and subentry.data["think"] is False,"model switch preserves prompt history and think settings")
            check(runtime(hass) is relay and relay.frames.fresh,"model settings preserve camera runtime and pairing session")
            for invalid in ({"revision":before["revision"]},{"keep_alive":-1},{"num_ctx":True},{"text_model":"qwen3-vl:8b-instruct"}):
                data={"action":"set","revision":saved["revision"],"text_model":"qwen3-vl:4b-instruct",
                    "vision_model":"qwen3-vl:4b-instruct","keep_alive":300,"num_ctx":2048,**invalid}
                try:
                    await models(data)
                except ServiceValidationError:
                    check(True,"invalid or stale model change rejected: "+str(invalid))
                else:
                    raise AssertionError("Invalid model settings accepted")
            await hass.services.async_call("jarvis_tablet_audio","describe_camera",{"source":"tablet"},blocking=True,return_response=True,context=Context(user_id=admin.id))
            check(vision_payloads[-1]["keep_alive"]==300 and vision_payloads[-1]["num_ctx"]==2048 and vision_payloads[-1]["model"]==subentry.data["model"],"vision shares text model residency and context")
            from .proactive import check_proactive
            await check_proactive(hass,relay,jpeg,device,nonce,admin,guest,worker_state,check)
            async with client.delete(base + "/frame", headers=headers) as response:
                check(response.status == 204, "stop clears image")
            check(hass.states.get(cid).state == "unavailable" and relay.frames.image is None, "no stale fallback after stop")
            async with client.post(base + "/frame", headers={**headers, "X-Relay-Sequence": "2"}, data=jpeg) as response:
                check(response.status == 409, "late frame after stop rejected")
        check(len(seen) == 9, "vision called only for explicit service/question")
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
