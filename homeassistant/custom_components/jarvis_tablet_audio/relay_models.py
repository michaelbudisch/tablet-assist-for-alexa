"""Administrator model settings, preserving existing Ollama prompts and camera sessions."""
import asyncio
import hashlib
import json

from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import entity_registry as er

VISION_MODELS = ("qwen3-vl:2b-instruct", "qwen3-vl:4b-instruct", "qwen3-vl:8b-instruct", "gemma3:4b")
TEXT_MODELS = ("qwen3:4b-instruct",) + VISION_MODELS
KEEP_ALIVE = (0, 60, 120, 300, 600)
CONTEXTS = (2048, 4096, 8192)
MODEL_OPTIONS = frozenset(("vision_model", "model_keep_alive", "model_num_ctx"))


def find_agent(hass):
    from .conversation import LLM_AGENT
    row = er.async_get(hass).async_get(LLM_AGENT)
    entry = hass.config_entries.async_get_entry(row.config_entry_id) if row else None
    subentry = entry.subentries.get(row.config_subentry_id) if entry and row.config_subentry_id else None
    if not entry or entry.domain != "ollama" or not subentry or subentry.subentry_type != "conversation":
        raise ServiceValidationError("Jarvis has no configured Ollama conversation agent")
    return entry, subentry


def settings(relay, subentry):
    return {"text_model": subentry.data.get("model"),
        "vision_model": relay.entry.options.get("vision_model", "qwen3-vl:4b-instruct"),
        "keep_alive": subentry.data.get("keep_alive", 120),
        "num_ctx": subentry.data.get("num_ctx", 4096),
        "vision_keep_alive": relay.entry.options.get("model_keep_alive", 0),
        "vision_num_ctx": relay.entry.options.get("model_num_ctx", 4096)}


def revision(values):
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


async def model_settings(relay, call):
    user = await relay.hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
    if not user or not user.is_admin:
        raise Unauthorized()
    from .const import DOMAIN
    from .relay_vision import request
    lock = relay.hass.data[DOMAIN].setdefault("model_settings_lock", asyncio.Lock())
    async with lock:
        entry, subentry = find_agent(relay.hass)
        runtime = await request(relay, "/runtime")
        if runtime.get("settings_api") != 1:
            raise ServiceValidationError("Update the GPU vision worker to 1.8.0")
        current = settings(relay, subentry)
        if call.data.get("action", "get") == "set":
            if relay.vision_lock.locked() or runtime.get("busy"):
                raise ServiceValidationError("Wait until the current camera description finishes")
            if call.data.get("revision") != revision(current):
                raise ServiceValidationError("Settings changed; refresh before saving")
            text, vision = call.data.get("text_model"), call.data.get("vision_model")
            keep, context = call.data.get("keep_alive"), call.data.get("num_ctx")
            if text not in TEXT_MODELS or text not in runtime.get("text_models", []):
                raise ServiceValidationError("Select an installed text model")
            if vision not in VISION_MODELS or vision not in runtime.get("vision_models", []):
                raise ServiceValidationError("Select an installed vision model")
            if type(keep) is not int or keep not in KEEP_ALIVE or type(context) is not int or context not in CONTEXTS:
                raise ServiceValidationError("Unsupported residency or context size")
            # Re-read after the network request, preserving unrelated prompt/tool/history settings.
            entry, subentry = find_agent(relay.hass)
            if revision(settings(relay, subentry)) != call.data["revision"]:
                raise ServiceValidationError("Settings changed; refresh before saving")
            options = {**relay.entry.options, "vision_model": vision,
                "model_keep_alive": keep, "model_num_ctx": context}
            data = {**subentry.data, "model": text, "keep_alive": keep, "num_ctx": context}
            relay.hass.config_entries.async_update_entry(relay.entry, options=options)
            # Native HA persistence and its normal update listener reload the Ollama entry.
            relay.hass.config_entries.async_update_subentry(entry, subentry, data=data)
            current = settings(relay, subentry)
        return {**current, "revision": revision(current),
            "shared": current["text_model"] == current["vision_model"],
            "text_models": [m for m in runtime.get("text_models", []) if m in TEXT_MODELS],
            "vision_models": [m for m in runtime.get("vision_models", []) if m in VISION_MODELS],
            "loaded": runtime.get("loaded", []), "saved": call.data.get("action") == "set"}
