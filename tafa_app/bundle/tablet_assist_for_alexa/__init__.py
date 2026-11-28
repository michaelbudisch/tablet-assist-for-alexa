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

from .const import DOMAIN, ROOMS, settings
from .app_settings import async_sync_from_app
from .device_admin_ws import device_admin_command
from .device_settings_ws import device_settings_subscribe
from .visual_ws import visual_subscribe, visual_identity
from .ambient_profiles_ws import ambient_profiles_command
from .ring_notice_ws import ring_notice_subscribe
from .tafa_notice_ws import notice_subscribe
from .vision_camera_ws import vision_camera_config
from .ha_provision import provision_manifest, resolve_manifest_entities
from .dashboard_config import async_get_dashboard, async_set_dashboard
from .announcement import audio_url, allowed_targets
from .reminders import Reminders
from .local_data import LocalData
from .tafa_modules import register as register_tafa_modules, unregister as unregister_tafa_modules
from .learning import Learning
from .learning_ws import learning_command
from .web_search import search_command
from .web_article import article_read_command
from homeassistant.components import websocket_api

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CONTROL_PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.SELECT]
PLATFORMS = [Platform.STT, Platform.TTS, Platform.CONVERSATION, Platform.CAMERA, Platform.BINARY_SENSOR, *CONTROL_PLATFORMS]
_LOGGER = logging.getLogger(__name__)
ANNOUNCE_SCHEMA = vol.Schema({
    vol.Required("text"): vol.All(cv.string, vol.Length(min=1, max=500)),
    vol.Required("rooms"): vol.All(cv.ensure_list, [vol.In(ROOMS)], vol.Length(min=1, max=len(ROOMS))),
})

async def async_setup(hass: HomeAssistant, config):
    websocket_api.async_register_command(hass, learning_command)
    websocket_api.async_register_command(hass, search_command)
    websocket_api.async_register_command(hass, article_read_command)
    websocket_api.async_register_command(hass, async_sync_from_app)
    websocket_api.async_register_command(hass, device_admin_command)
    websocket_api.async_register_command(hass, device_settings_subscribe)
    websocket_api.async_register_command(hass, visual_subscribe)
    websocket_api.async_register_command(hass, visual_identity)
    websocket_api.async_register_command(hass, ambient_profiles_command)
    websocket_api.async_register_command(hass, ring_notice_subscribe)
    websocket_api.async_register_command(hass, notice_subscribe)
    websocket_api.async_register_command(hass, vision_camera_config)
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
        StaticPathConfig("/tablet_assist_for_alexa/ambient_night.js", str(Path(__file__).parent / "frontend" / "ambient_night.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/ambient_overview.js", str(Path(__file__).parent / "frontend" / "ambient_overview.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/ambient_profiles_client.js", str(Path(__file__).parent / "frontend" / "ambient_profiles_client.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/ring_ui.js", str(Path(__file__).parent / "frontend" / "ring_ui.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/response_overlay.js", str(Path(__file__).parent / "frontend" / "response_overlay.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/visual_client.js", str(Path(__file__).parent / "frontend" / "visual_client.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/dashboard_model.js", str(Path(__file__).parent / "frontend" / "dashboard_model.js"), False),
        StaticPathConfig("/tablet_assist_for_alexa/voice_tools.js", str(Path(__file__).parent / "frontend" / "voice_tools.js"), False),
    ])
    return True

async def async_setup_entry(hass, entry):
    # Migrate only the previous default label, never a user-customized title.
    if entry.title == "Tablet Assist for Alexa":
        hass.config_entries.async_update_entry(entry, title="TAFA")
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
    # TAFA betreibt Audio und Wakeword ausschließlich im eigenen Namensraum.
    from .relay.relay_room_adapter import setup_room_audio
    from .relay.relay_wake_devices import setup_wake_devices
    await setup_room_audio(hass, entry)
    await setup_wake_devices(hass, entry)
    data["relay_started"] = True
    # TAFA registriert Kamera, Audio und Geräte direkt.
    from .relay.relay_camera import async_setup as setup_relay_camera
    await setup_relay_camera(hass, entry)
    data["relay_camera_started"] = True
    active_platforms = PLATFORMS
    data.setdefault("active_platforms", {})[entry.entry_id] = active_platforms
    await hass.config_entries.async_forward_entry_setups(entry, active_platforms)
    hass.services.async_register(DOMAIN, "announce", announce, schema=ANNOUNCE_SCHEMA)
    register_tafa_modules(hass, entry)
    # No extra TAFA sidebar/dashboard. The Supervisor App is the only
    # configuration and speech-control user interface.
    await reminders.load()
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True

async def _reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    active_platforms = hass.data.get(DOMAIN, {}).get("active_platforms", {}).pop(
        entry.entry_id, PLATFORMS)
    ok = await hass.config_entries.async_unload_platforms(entry, active_platforms)
    if ok:
        if hass.data.get(DOMAIN, {}).pop("relay_started", False):
            from .relay.relay_room_adapter import unload_room_audio
            from .relay.relay_wake_devices import unload_wake_devices
            if hass.data.get(DOMAIN, {}).pop("relay_camera_started", False):
                from .relay.relay_camera import async_unload as unload_relay_camera
                unload_relay_camera(hass)
            unload_room_audio(hass)
            unload_wake_devices(hass)
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data:
            data.reminders.close()
        hass.services.async_remove(DOMAIN, "announce")
        unregister_tafa_modules(hass)
    return ok
