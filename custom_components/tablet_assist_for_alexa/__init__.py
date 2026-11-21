"""Tablet speech processing and optional Alexa announcements."""
import asyncio
from pathlib import Path

import aiohttp
import voluptuous as vol
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.components.http import StaticPathConfig

from .const import DOMAIN, ROOMS, settings
from .announcement import audio_url, allowed_targets

PLATFORMS = [Platform.STT, Platform.TTS, Platform.CONVERSATION]
ANNOUNCE_SCHEMA = vol.Schema({
    vol.Required("text"): vol.All(cv.string, vol.Length(min=1, max=500)),
    vol.Required("rooms"): vol.All(cv.ensure_list, [vol.In(ROOMS)], vol.Length(min=1, max=len(ROOMS))),
})

async def async_setup(hass: HomeAssistant, config):
    # All files required at runtime are part of this integration's directory.
    await hass.http.async_register_static_paths([
        StaticPathConfig("/tablet_assist_for_alexa/keepalive.js", str(Path(__file__).parent / "frontend" / "keepalive.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/assist.js", str(Path(__file__).parent / "frontend" / "assist.js"), False),
    ])
    return True

async def async_setup_entry(hass, entry):
    cfg = settings(entry)
    lock = asyncio.Lock()
    session = async_get_clientsession(hass)

    async def announce(call: ServiceCall):
        msg = call.data["text"].strip()
        if not msg or not cfg.get("rooms") or not cfg.get("mp3_base") or not cfg.get("mp3_token") or not cfg.get("public_audio_base"):
            raise HomeAssistantError("Configure optional Alexa announcements first.")
        # Never play to unconfigured/quiet/unavailable rooms.
        async with lock:
            targets = allowed_targets(cfg["rooms"], call.data["rooms"], hass.states.get)
            if not targets:
                raise HomeAssistantError("No enabled announcement targets.")
            try:
                async with session.post(cfg["mp3_base"]+"/generate",
                    json={"text":msg, "profile":cfg["hardware_profile"], "voice_variant":cfg["voice_variant"],
                          "sound_profile":cfg["mp3_profile"], "chime":cfg["chime"]},
                    headers={"X-API-Key":cfg["mp3_token"]},
                    timeout=aiohttp.ClientTimeout(total=120), allow_redirects=False) as response:
                    if response.status != 200:
                        raise ValueError("Generation failed")
                    body = await response.json()
                    url = audio_url(cfg["public_audio_base"], body)
            except (aiohttp.ClientError, TimeoutError, ValueError, TypeError, AttributeError) as exc:
                raise HomeAssistantError("MP3 generation failed.") from None
            targets = allowed_targets(cfg["rooms"], call.data["rooms"], hass.states.get)
            if not targets:
                raise HomeAssistantError("Targets became quiet or unavailable.")
            await hass.services.async_call("notify", "send_message",
                {"entity_id":targets, "message":f'<audio src="{url}"/>'}, blocking=True, context=call.context)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.services.async_register(DOMAIN, "announce", announce, schema=ANNOUNCE_SCHEMA)
    return True

async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.services.async_remove(DOMAIN, "announce")
    return ok
