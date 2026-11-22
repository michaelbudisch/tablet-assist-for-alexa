"""Independent native audio delivery for Assist tablets."""
from homeassistant.const import Platform

PLATFORMS = [Platform.TTS, Platform.CONVERSATION, Platform.CAMERA, Platform.BINARY_SENSOR]


async def async_setup_entry(hass, entry):
    from .relay_camera import async_setup
    await async_setup(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    options = dict(entry.options)
    async def reload_options(hass, updated):
        if dict(updated.options) != options:
            await hass.config_entries.async_reload(updated.entry_id)
    entry.async_on_unload(entry.add_update_listener(reload_options))
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        from .relay_camera import async_unload
        async_unload(hass)
    return unloaded
