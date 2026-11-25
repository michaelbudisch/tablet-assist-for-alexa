"""Motion entities for explicitly enabled tablet cameras."""
async def async_setup_entry(hass, entry, async_add_entities):
    if hass.data.get("tablet_assist_for_alexa", {}).get("relay_started"):
        from .relay.binary_sensor import async_setup_entry as setup
        await setup(hass, entry, async_add_entities)
