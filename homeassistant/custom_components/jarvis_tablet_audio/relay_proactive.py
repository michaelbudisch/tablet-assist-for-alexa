"""Opt-in motion checks, fixed detections and explicitly configured actions."""
import asyncio
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta
from time import monotonic
from uuid import uuid4

from homeassistant.core import Context
from homeassistant.exceptions import ServiceValidationError, Unauthorized, HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .relay_vision import request, resolve_camera

EVENT = "jarvis_echo_relay_proactive"
DETECTION_EVENT = "jarvis_echo_relay_detection"
DEFAULTS = {"enabled": False, "test_mode": True, "cooldown": 60, "start": "06:00", "end": "10:00",
    "classes": ["person", "dog"], "greeting": True, "greeting_class": "adult", "name": "",
    "offer_overview": True, "weather_entity": "", "script_entity": ""}
PROACTIVE_OPTIONS = frozenset(("proactive_settings",))
CLASSES = ("person", "adult", "child", "dog")


def validate_settings(values):
    if not isinstance(values, dict) or set(values) != set(DEFAULTS):
        raise ServiceValidationError("Invalid proactive settings")
    for key in ("enabled", "test_mode", "greeting", "offer_overview"):
        if type(values[key]) is not bool:
            raise ServiceValidationError("Invalid switch")
    if type(values["cooldown"]) is not int or values["cooldown"] not in (30, 60, 120, 300, 600, 1800):
        raise ServiceValidationError("Invalid cooldown")
    for key in ("start", "end"):
        if not isinstance(values[key], str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", values[key]):
            raise ServiceValidationError("Invalid time")
    classes = values["classes"]
    if not isinstance(classes, list) or not classes or len(classes) > 4 or any(type(c) is not str or c not in CLASSES for c in classes) or len(set(classes)) != len(classes):
        raise ServiceValidationError("Select supported classes")
    if values["greeting_class"] not in ("person", "adult", "child"):
        raise ServiceValidationError("Invalid greeting class")
    name = values["name"]
    if not isinstance(name, str) or len(name) > 40 or any(not (c.isalpha() or c in " '-") for c in name):
        raise ServiceValidationError("Invalid fixed greeting name")
    for key, domain in (("weather_entity", "weather"), ("script_entity", "script")):
        if not isinstance(values[key], str) or values[key] and not re.fullmatch(domain + r"\.[a-z0-9_]+", values[key]):
            raise ServiceValidationError("Invalid configured entity")
    return {**values, "name": name.strip()}


def validate_detection(value):
    if not isinstance(value, dict) or set(value) != {"person_count", "dog_count", "age_groups", "uncertain"}:
        raise ServiceValidationError("Invalid detection")
    if any(type(value[k]) is not int or not 0 <= value[k] <= 10 for k in ("person_count", "dog_count")) or type(value["uncertain"]) is not bool:
        raise ServiceValidationError("Invalid detection")
    groups = value["age_groups"]
    if not isinstance(groups, list) or len(groups) > 3 or any(type(g) is not str or g not in ("adult", "child", "unknown") for g in groups) or len(set(groups)) != len(groups):
        raise ServiceValidationError("Invalid age groups")
    if (value["person_count"] == 0 and groups) or (value["person_count"] > 0 and not groups):
        raise ServiceValidationError("Inconsistent detection")
    labels = (["person"] + [g for g in groups if g != "unknown"] if value["person_count"] else []) + (["dog"] if value["dog_count"] else [])
    return [] if value["uncertain"] else labels


class Proactive:
    def __init__(self, relay):
        self.relay, self.hass = relay, relay.hass
        self.lock = asyncio.Lock()
        self.clients = {}
        self.pending = None
        self.last_attempt = None
        self.last = {"status": "idle"}
        self.greeted_date = None
        self.store = Store(self.hass, 1, DOMAIN + ".proactive." + relay.entry.entry_id)

    async def setup(self):
        saved = await self.store.async_load()
        if isinstance(saved, dict):
            self.greeted_date = saved.get("greeted_date")

    @property
    def settings(self):
        return {**DEFAULTS, **self.relay.entry.options.get("proactive_settings", {})}

    @property
    def revision(self):
        return hashlib.sha256(json.dumps(self.settings, sort_keys=True).encode()).hexdigest()

    def snapshot(self):
        states = self.hass.states.async_all()
        return {**self.settings, "revision": self.revision, "last": self.last, "greeted_date": self.greeted_date,
            "weather_entities": [{"entity_id": s.entity_id, "name": s.name} for s in states if s.domain == "weather"][:100],
            "script_entities": [{"entity_id": s.entity_id, "name": s.name} for s in states if s.domain == "script"][:200]}

    def eligible_clients(self):
        now = monotonic()
        self.clients = {key: value for key, value in self.clients.items() if now - value["seen"] < 25}
        return any(not c["busy"] for c in self.clients.values())

    def status(self, name, **values):
        self.last = {"status": name, "at": dt_util.utcnow().isoformat(), **values}
        return self.last

    async def user(self, context, admin=False):
        user = await self.hass.auth.async_get_user(context.user_id) if context.user_id else None
        if user is None or admin and not user.is_admin:
            raise Unauthorized()
        if not admin:
            await resolve_camera(self.relay, "tablet", context)
        return user

    async def service(self, call):
        action, data = call.data.get("action", "get"), call.data
        if action in ("get", "set"):
            await self.user(call.context, admin=True)
            if action == "set":
                if data.get("revision") != self.revision:
                    raise ServiceValidationError("Settings changed; refresh")
                values = validate_settings(data.get("settings"))
                for key in ("weather_entity", "script_entity"):
                    if values[key] and self.hass.states.get(values[key]) is None:
                        raise ServiceValidationError("Configured entity not found")
                self.hass.config_entries.async_update_entry(self.relay.entry,
                    options={**self.relay.entry.options, "proactive_settings": values})
                self.pending = None
            return self.snapshot()
        if action == "check":
            if call.context.user_id:
                await self.user(call.context, admin=True)
            return await self.inspect(call.context, manual=data.get("manual", False))
        await self.user(call.context)
        client = data.get("client_id", "")
        if not isinstance(client, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", client):
            raise ServiceValidationError("Invalid client")
        if action == "heartbeat":
            self.eligible_clients()
            if client in self.clients and self.clients[client]["user_id"] != call.context.user_id:
                raise Unauthorized()
            if client not in self.clients and len(self.clients) >= 16:
                raise ServiceValidationError("Too many clients")
            self.clients[client] = {"seen": monotonic(), "busy": data.get("busy", True), "user_id": call.context.user_id}
            return {"enabled": self.settings["enabled"]}
        job = self.pending
        if not self.settings["enabled"] or not job or job["id"] != data.get("request_id") or monotonic() - job["created"] > 90 or job["revision"] != self.revision:
            return {"accepted": False}
        if action == "claim":
            if job["client"] or client not in self.clients or self.clients[client]["user_id"] != call.context.user_id or self.clients[client]["busy"] or monotonic() - self.clients[client]["seen"] >= 25:
                return {"accepted": False}
            engine = er.async_get(self.hass).async_get_entity_id("tts", DOMAIN, self.relay.entry.entry_id + "_stream")
            if engine is None:
                return {"accepted": False}
            from homeassistant.components.tts import async_create_stream
            stream = async_create_stream(self.hass, engine, language="de")
            stream.async_set_message(job["message"])
            job["client"], job["user_id"] = client, call.context.user_id
            self.status("claimed", labels=job["labels"])
            return {"accepted": True, "message": job["message"], "offer_overview": job["offer_overview"],
                "audio_path": stream.url}
        if action == "ack" and job["client"] == client and job["user_id"] == call.context.user_id:
            if data.get("started"):
                await self.mark_action()
                self.status("greeting_started", labels=job["labels"])
            else:
                self.status("playback_skipped", labels=job["labels"])
            self.pending = None
            return {"accepted": True}
        return {"accepted": False}

    async def mark_action(self):
        self.greeted_date = dt_util.now().date().isoformat()
        await self.store.async_save({"greeted_date": self.greeted_date})

    async def message(self, settings, context):
        hour = dt_util.now().hour
        greeting = "Guten Morgen" if 5 <= hour < 11 else "Guten Tag" if 11 <= hour < 18 else "Guten Abend"
        text = greeting + (", " + settings["name"] if settings["name"] else "") + "."
        entity = settings["weather_entity"]
        if entity:
            try:
                state = self.hass.states.get(entity)
                kind = "hourly" if state and state.attributes.get("supported_features", 0) & 2 else "daily"
                async with asyncio.timeout(5):
                    result = await self.hass.services.async_call("weather", "get_forecasts", {"entity_id": entity, "type": kind}, blocking=True, return_response=True, context=context)
                forecasts = result.get(entity, {}).get("forecast", [])
                now = dt_util.now()
                relevant = []
                for item in forecasts:
                    stamp = dt_util.parse_datetime(str(item.get("datetime", "")))
                    if not stamp:
                        continue
                    local = dt_util.as_local(stamp)
                    if kind == "daily" and local.date() == now.date() or kind == "hourly" and now - timedelta(hours=1) <= local <= now + timedelta(hours=6):
                        relevant.append(item)
                rain = any(item.get("condition") in ("rainy", "pouring", "lightning-rainy", "snowy-rainy") or type(item.get("precipitation_probability")) in (int, float) and item["precipitation_probability"] >= 50 for item in relevant)
                if rain:
                    text += " Laut Vorhersage könnte es " + ("in den nächsten Stunden" if kind == "hourly" else "heute") + " regnen. Denk an deinen Regenschirm."
            except (HomeAssistantError, TimeoutError, ValueError, TypeError, AttributeError):
                pass
        if settings["offer_overview"]:
            text += " Möchtest du deinen Tagesüberblick hören?"
        return text

    async def inspect(self, context, manual=False):
        settings = self.settings
        if not settings["enabled"]:
            return self.status("disabled")
        if self.lock.locked() or self.relay.vision_lock.locked():
            return self.status("busy")
        now = dt_util.now()
        if not settings["test_mode"]:
            current = now.strftime("%H:%M")
            start, end = settings["start"], settings["end"]
            in_window = start <= current < end if start < end else current >= start or current < end
            if not in_window:
                return self.status("outside_window")
            if self.greeted_date == now.date().isoformat():
                return self.status("already_today")
        cooldown = settings["cooldown"] if settings["test_mode"] else max(300, settings["cooldown"])
        if self.last_attempt is not None and monotonic() - self.last_attempt < cooldown:
            return self.status("cooldown")
        if not self.relay.frames.fresh or not manual and self.relay.frames.motion is not True:
            return self.status("no_fresh_motion")
        if settings["greeting"] and not settings["script_entity"] and not self.eligible_clients():
            return self.status("no_idle_dashboard")
        async with self.lock:
            self.last_attempt = monotonic()
            revision = self.revision
            try:
                runtime = await request(self.relay, "/runtime")
                if runtime.get("busy"):
                    return self.status("busy")
                if runtime.get("detection_api") != 1:
                    return self.status("worker_update_required")
                model = self.relay.entry.options.get("vision_model", "qwen3-vl:4b-instruct")
                if model not in runtime.get("vision_models", []):
                    return self.status("worker_unavailable")
                async with self.relay.vision_lock:
                    frames = self.relay.frames
                    if not frames.fresh:
                        return self.status("no_fresh_motion")
                    received, session = frames.received, frames.session
                    result = await request(self.relay, "/detect", {"image": base64.b64encode(frames.image).decode("ascii"), "model": model,
                        "keep_alive": self.relay.entry.options.get("model_keep_alive", 0), "num_ctx": self.relay.entry.options.get("model_num_ctx", 4096)})
                if revision != self.revision or frames.session != session or not frames.fresh or frames.clock() - received > 15:
                    return self.status("expired")
                if result.get("detection_api") != 1:
                    return self.status("worker_update_required")
                labels = validate_detection(result.get("detection"))
                if not labels:
                    return self.status("uncertain" if result["detection"]["uncertain"] else "empty")
                matched = [value for value in labels if value in settings["classes"]]
                if not matched:
                    return self.status("no_match", labels=labels)
                entity = self.relay.camera_id()
                detection = {"labels": labels, "camera_entity_id": entity, "detection": result["detection"], "test_mode": settings["test_mode"]}
                self.hass.bus.async_fire(DETECTION_EVENT, detection, context=context)
                if settings["script_entity"]:
                    await self.hass.services.async_call("script", "turn_on", {"entity_id": settings["script_entity"], "variables": {"jarvis_detection": detection}}, blocking=True, context=context)
                    await self.mark_action()
                if settings["greeting"] and settings["greeting_class"] in labels and self.eligible_clients():
                    message = await self.message(settings, context)
                    if revision != self.revision or not self.eligible_clients():
                        return self.status("busy", labels=labels)
                    self.pending = {"id": uuid4().hex, "created": monotonic(), "revision": revision, "client": None,
                        "message": message, "offer_overview": settings["offer_overview"], "labels": labels}
                    self.hass.bus.async_fire(EVENT, {"request_id": self.pending["id"], "camera_entity_id": entity}, context=context)
                return self.status("detected", labels=labels)
            except (HomeAssistantError, TimeoutError, ValueError, KeyError, TypeError):
                return self.status("worker_unavailable")
