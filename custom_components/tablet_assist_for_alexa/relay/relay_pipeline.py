"""Camera-only pipeline diagnostic using the same intent path as dashboard Assist."""
import asyncio

from homeassistant.components.assist_pipeline.pipeline import PipelineInput, PipelineRun, PipelineStage, async_get_pipeline
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers import chat_session, entity_registry as er

from .const import DOMAIN
from .relay_vision import classify


async def run_intent(hass, pipeline, context, text):
    events = []
    run = PipelineRun(hass=hass, context=context, pipeline=pipeline,
        start_stage=PipelineStage.INTENT, end_stage=PipelineStage.INTENT,
        event_callback=events.append)
    with chat_session.async_get_chat_session(hass, None, context=None) as session:
        request = PipelineInput(run=run, session=session, intent_input=text)
        async with asyncio.timeout(120):
            await request.execute(validate=True)
    ended = next((e.data for e in events if e.type == "intent-end"), {})
    output = ended.get("intent_output", {})
    speech = output.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")
    errors = [e.data for e in events if e.type == "error"]
    return {"pipeline_id": pipeline.id, "pipeline_run_id": run.id,
        "prefer_local_intents": pipeline.prefer_local_intents,
        "processed_locally": ended.get("processed_locally"),
        "speech": speech, "errors": errors}


async def check_camera_pipeline(relay, call):
    user = await relay.hass.auth.async_get_user(call.context.user_id) if call.context.user_id else None
    if user is None or not user.is_admin:
        raise Unauthorized()
    text = call.data["text"]
    if classify(text) is None:
        raise ServiceValidationError("Diagnostic accepts camera questions only")
    pipeline = async_get_pipeline(relay.hass, call.data.get("pipeline_id"))
    agent = er.async_get(relay.hass).async_get_entity_id("conversation", "tablet_assist_for_alexa", relay.entry.entry_id + "_conversation_router")
    if pipeline.conversation_engine != agent:
        raise ServiceValidationError("Select the TAFA conversation router pipeline")
    return await run_intent(relay.hass, pipeline, call.context, text)
