"""Independent native audio delivery for Assist tablets."""
from homeassistant.const import Platform

PLATFORMS = [Platform.TTS, Platform.CONVERSATION]


async def async_setup_entry(hass, entry):
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
