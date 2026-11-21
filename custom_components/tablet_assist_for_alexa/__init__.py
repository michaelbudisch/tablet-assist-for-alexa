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
from homeassistant.components import frontend, panel_custom

from .const import DOMAIN, ROOMS, settings
from .announcement import audio_url, allowed_targets
from .reminders import Reminders
from .local_data import LocalData

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
        StaticPathConfig("/tablet_assist_for_alexa/panel.js", str(Path(__file__).parent / "frontend" / "panel.js"), False),
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

    reminders = Reminders(hass, entry, cfg)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = LocalData(hass, cfg, reminders)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.services.async_register(DOMAIN, "announce", announce, schema=ANNOUNCE_SCHEMA)
    await panel_custom.async_register_panel(
        hass, webcomponent_name="tablet-assist-panel", frontend_url_path=DOMAIN,
        sidebar_title="Tablet Assist", sidebar_icon="mdi:microphone-message",
        module_url="/tablet_assist_for_alexa/panel.js?v=0.3.0",
        config={"rooms": list(cfg.get("rooms", {})), "sources": list(cfg.get("sources", {})), "reminders": bool(cfg.get("reminders_enabled"))}, require_admin=False,
    )
    await reminders.load()
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True

async def _reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data:
            data.reminders.close()
        hass.services.async_remove(DOMAIN, "announce")
        frontend.async_remove_panel(hass, DOMAIN)
    return ok
