"""Local command fallback after explicit Jarvis camera/dialogue routing."""
import asyncio

from homeassistant.components import conversation


async def native_reply(hass, user_input):
    """Keep native HA commands available with pipeline local preference disabled."""
    async with asyncio.timeout(10):
        result = await conversation.async_converse(
            hass=hass, text=user_input.text, conversation_id=None,
            context=user_input.context, language=user_input.language,
            agent_id=conversation.HOME_ASSISTANT_AGENT,
            device_id=user_input.device_id, satellite_id=user_input.satellite_id,
        )
    return None if result.response.as_dict().get("response_type") == "error" else result
