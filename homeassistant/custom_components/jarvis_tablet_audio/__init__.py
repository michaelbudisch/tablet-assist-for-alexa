"""Independent native audio delivery for Assist tablets."""
from homeassistant.const import Platform

PLATFORMS = [Platform.TTS, Platform.CONVERSATION, Platform.CAMERA, Platform.BINARY_SENSOR]


async def async_setup_entry(hass, entry):
    # Purge obsolete credentials from existing legacy configuration entries.
    if "qwen_token" in entry.data:
        hass.config_entries.async_update_entry(
            entry, data={k: v for k, v in entry.data.items() if k != "qwen_token"}
        )
    from .relay_camera import async_setup
    await async_setup(hass, entry)
    from .relay_room_adapter import setup_room_audio
    await setup_room_audio(hass, entry)
    from .relay_wake_devices import setup_wake_devices
    await setup_wake_devices(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    options = dict(entry.options)
    from .relay_models import MODEL_OPTIONS
    from .relay_proactive import PROACTIVE_OPTIONS
    async def reload_options(hass, updated):
        if {k: v for k, v in updated.options.items() if k not in MODEL_OPTIONS | PROACTIVE_OPTIONS} != {k: v for k, v in options.items() if k not in MODEL_OPTIONS | PROACTIVE_OPTIONS}:
            await hass.config_entries.async_reload(updated.entry_id)
    entry.async_on_unload(entry.add_update_listener(reload_options))
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        from .relay_camera import async_unload
        async_unload(hass)
        from .relay_room_adapter import unload_room_audio
        unload_room_audio(hass)
        from .relay_wake_devices import unload_wake_devices
        unload_wake_devices(hass)
    return unloaded
