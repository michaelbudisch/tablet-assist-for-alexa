"""Tablet speech processing and optional Alexa announcements."""
import asyncio
import logging
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
from .app_settings import async_sync_from_app
from .ha_provision import provision_manifest, resolve_manifest_entities
from .dashboard_config import async_get_dashboard, async_set_dashboard
from .announcement import audio_url, allowed_targets
from .reminders import Reminders
from .local_data import LocalData
from .learning import Learning
from .learning_ws import learning_command
from homeassistant.components import websocket_api

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.STT, Platform.TTS, Platform.CONVERSATION, Platform.CAMERA, Platform.BINARY_SENSOR]
_LOGGER = logging.getLogger(__name__)
ANNOUNCE_SCHEMA = vol.Schema({
    vol.Required("text"): vol.All(cv.string, vol.Length(min=1, max=500)),
    vol.Required("rooms"): vol.All(cv.ensure_list, [vol.In(ROOMS)], vol.Length(min=1, max=len(ROOMS))),
})

async def async_setup(hass: HomeAssistant, config):
    websocket_api.async_register_command(hass, learning_command)
    websocket_api.async_register_command(hass, async_sync_from_app)
    websocket_api.async_register_command(hass, provision_manifest)
    websocket_api.async_register_command(hass, resolve_manifest_entities)
    websocket_api.async_register_command(hass, async_get_dashboard)
    websocket_api.async_register_command(hass, async_set_dashboard)
    # All files required at runtime are part of this integration's directory.
    await hass.http.async_register_static_paths([
        StaticPathConfig("/tablet_assist_for_alexa/keepalive.js", str(Path(__file__).parent / "frontend" / "keepalive.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/assist.js", str(Path(__file__).parent / "frontend" / "assist.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/room_assist_test.js", str(Path(__file__).parent / "frontend" / "room_assist_test.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/device_audio.js", str(Path(__file__).parent / "frontend" / "device_audio.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/panel.js", str(Path(__file__).parent / "frontend" / "panel.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/brand.svg", str(Path(__file__).parent / "frontend" / "brand.svg"), False),
        StaticPathConfig("/tablet_assist_for_alexa/dashboard.js", str(Path(__file__).parent / "frontend" / "dashboard.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/dashboard_model.js", str(Path(__file__).parent / "frontend" / "dashboard_model.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/voice_tools.js", str(Path(__file__).parent / "frontend" / "voice_tools.js"), False),
    ])
    return True

async def async_setup_entry(hass, entry):
    cfg = settings(entry)
    lock = asyncio.Lock()
    session = async_get_clientsession(hass)

    async def announce(call: ServiceCall):
        msg = call.data["text"].strip()
        if not msg or not cfg.get("rooms") or not cfg.get("mp3_base") or not cfg.get("public_audio_base"):
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
                    headers={},
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
    learning = Learning(hass, entry, cfg)
    await learning.load()
    data = hass.data.setdefault(DOMAIN, {})
    data[entry.entry_id] = LocalData(hass, cfg, reminders, learning)
    # Device Bridge REST paths and legacy service names are owned by the new
    # single integration. Never register duplicate views if an older Jarvis
    # Tablet Audio integration is still configured in this Home Assistant.
    legacy_present = bool(hass.config_entries.async_entries("jarvis_tablet_audio"))
    data["relay_started"] = not legacy_present
    if legacy_present:
        _LOGGER.warning("Legacy Jarvis Tablet Audio detected; integrated relay disabled to avoid duplicate API routes. Migrate the old integration before enabling the unified backend.")
    else:
        from .relay.relay_camera import async_setup as setup_relay_camera
        from .relay.relay_room_adapter import setup_room_audio
        from .relay.relay_wake_devices import setup_wake_devices
        await setup_relay_camera(hass, entry)
        await setup_room_audio(hass, entry)
        await setup_wake_devices(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.services.async_register(DOMAIN, "announce", announce, schema=ANNOUNCE_SCHEMA)
    await panel_custom.async_register_panel(
        hass, webcomponent_name="tablet-assist-panel", frontend_url_path=DOMAIN,
        sidebar_title="TAFA Dashboard", sidebar_icon="mdi:view-dashboard-outline",
        module_url="/tablet_assist_for_alexa/panel.js?v=0.4.16",
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
        if hass.data.get(DOMAIN, {}).pop("relay_started", False):
            from .relay.relay_camera import async_unload as unload_relay_camera
            from .relay.relay_room_adapter import unload_room_audio
            from .relay.relay_wake_devices import unload_wake_devices
            unload_relay_camera(hass)
            unload_room_audio(hass)
            unload_wake_devices(hass)
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data:
            data.reminders.close()
        hass.services.async_remove(DOMAIN, "announce")
        frontend.async_remove_panel(hass, DOMAIN)
    return ok
