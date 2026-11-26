"""Test-only integration. Never ship to a user's HA installation."""
import asyncio
import json
import os
from pathlib import Path
import traceback
from aiohttp import web
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Context
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.components import conversation, frontend
from homeassistant.components.persistent_notification.helpers import async_register_callback
from homeassistant.util import dt as dt_util

DOMAIN = "tablet_assist_for_alexa"
PHASE = os.environ["TABLET_ASSIST_CI_PHASE"]
MARKER = "CI test reminder"
CHECKS = []

def check(condition, label):
    if not condition:
        raise AssertionError(label)
    CHECKS.append(label)
    print("CI PASS:", label, flush=True)

async def wait_until(predicate, label, seconds=60):
    async with asyncio.timeout(seconds):
        while not predicate():
            await asyncio.sleep(0.2)
    check(True, label)

async def entry_loaded(hass, entry):
    await wait_until(lambda: hass.config_entries.async_get_entry(entry.entry_id).state == ConfigEntryState.LOADED, entry.domain+" loaded")

async def create_entry(hass, domain, data):
    flow = await hass.config_entries.flow.async_init(domain, context={"source":"user"})
    check(flow["type"]=="form", domain+" configuration form")
    result = await hass.config_entries.flow.async_configure(flow["flow_id"], data)
    check(result["type"]=="create_entry", domain+" configuration accepted: "+str(result.get("errors",{})))
    entry = result["result"]
    await entry_loaded(hass, entry)
    return entry

def entity(hass, entry, domain):
    records = er.async_entries_for_config_entry(er.async_get(hass),entry.entry_id)
    return next(r.entity_id for r in records if r.domain==domain)

async def converse(hass, agent, text, previous=None):
    response = await conversation.async_converse(hass, text=text, conversation_id=previous, context=Context(), language="de", agent_id=agent)
    data=response.response.as_dict()
    check(data.get("response_type")!="error", "conversation: "+text)
    speech=data["speech"]["plain"]["speech"]
    return speech,response.conversation_id,response.continue_conversation

async def phase_one(hass):
    # A local fake health endpoint, no TTS model, no devices or accounts.
    app=web.Application()
    async def health(_request):return web.json_response({"ready":True})
    app.router.add_get("/health",health)
    runner=web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner,"127.0.0.1",15001).start()
    try:
        # Synthetic entity-registry row to exercise the actual config-flow validation.
        # This is NOT a functioning Wyoming STT engine.
        row=er.async_get(hass).async_get_or_create("stt","wyoming","tablet_assist_ci_stt",suggested_object_id="ci_stt")
        todo=await create_entry(hass,"local_todo",{"todo_list_name":"CI Shopping"})
        todo_id=entity(hass,todo,"todo")
        entry=await create_entry(hass,DOMAIN,{
            "piper_base":"http://127.0.0.1:15001","cpu_stt":row.entity_id,
            "hardware_profile":"cpu","live_profile":"natural","voice_variant":"default",
            "conversation_mode":"intelligent","mp3_profile":"natural","chime":False,
        })
        check(entry.data["hardware_profile"]=="Homeserver","translated config value compatible")
        check(DOMAIN not in hass.data[frontend.DATA_PANELS],"no TAFA sidebar registered")
        check(hass.services.has_service(DOMAIN,"announce"),"service registered")
        relay=hass.data.get(DOMAIN,{})
        check(bool(relay.get("relay_camera")),"unified native camera relay registered")
        check(bool(relay.get("wake_devices_dynamic")),"native wake-device registry registered")
        # Enrolling a new tablet must create real Home Assistant entities at
        # runtime, without static helper slots or a Core restart.
        controller=relay["wake_devices_dynamic"]
        tablet_id="c"*32
        controller.devices[tablet_id]={
            "device_id":tablet_id, "user_id":"ci-device",
            "room":"CI Tablet", "muted":False, "mic_gain":100,
            "screen_awake":True, "word":"Jarvis"}
        controller.changed(tablet_id,registered=True)
        def tablet_entity(key):
            registry=er.async_get(hass)
            match=next((e.entity_id for e in registry.entities.values()
                        if e.unique_id=="tafa_"+tablet_id+"_"+key),None)
            return match
        await wait_until(lambda: tablet_entity("mic_gain") is not None
                         and tablet_entity("online") is not None
                         and tablet_entity("muted") is not None,
                         "tablet sensors, numbers and switches registered dynamically")
        await controller.set_value(tablet_id,"mic_gain",120)
        await wait_until(lambda: hass.states.get(tablet_entity("mic_gain")) is not None
                         and hass.states.get(tablet_entity("mic_gain")).state in ("120","120.0"),
                         "HA tablet control updates state")
        check(bool(relay.get("room_audio")),"multiroom audio transport registered")
        check(hass.services.has_service(DOMAIN,"room_audio"),"TAFA room audio service")
        check(hass.services.has_service(DOMAIN,"model_settings"),"unified AI model settings service")
        check(bool(entity(hass,entry,"camera")),"native camera entity registered")
        check(bool(entity(hass,entry,"binary_sensor")),"native motion entity registered")
        agent=entity(hass,entry,"conversation")
        check(bool(entity(hass,entry,"stt")) and bool(entity(hass,entry,"tts")),"STT and TTS entities registered")
        # Real HA state machine, synthetic state readings.
        hass.states.async_set("sensor.ci_flow","40",{"unit_of_measurement":"°C"})
        hass.states.async_set("sensor.ci_return","36",{"unit_of_measurement":"°C"})
        hass.states.async_set("weather.ci_weather","cloudy",{"temperature":7,"temperature_unit":"°C"})
        before=hass.data[DOMAIN][entry.entry_id]
        flow=await hass.config_entries.options.async_init(entry.entry_id)
        check(flow["type"]=="menu","categorized TAFA options menu")
        flow=await hass.config_entries.options.async_configure(flow["flow_id"],{"next_step_id":"sources"})
        check(flow["type"]=="form","data-source options form")
        result=await hass.config_entries.options.async_configure(flow["flow_id"],{
            "vorlauf":"sensor.ci_flow","ruecklauf":"sensor.ci_return","weather":"weather.ci_weather","shopping":todo_id,
            "reminders_enabled":True,"learning_enabled":True,
        })
        check(result["type"]=="create_entry","data sources accepted: "+str(result.get("errors",{})))
        await wait_until(lambda: hass.data.get(DOMAIN,{}).get(entry.entry_id) not in (None,before) and entry.state==ConfigEntryState.LOADED,"options reload")
        data=hass.data[DOMAIN][entry.entry_id]
        check(data.sources.get("shopping")==todo_id and data.cfg.get("reminders_enabled"),"options live")
        check(DOMAIN not in hass.data[frontend.DATA_PANELS],"no TAFA sidebar after reload")
        menu=await hass.config_entries.options.async_init(entry.entry_id)
        check(menu["type"]=="menu","hardware setup reachable from categorized options")
        hardware=await hass.config_entries.options.async_configure(menu["flow_id"],{"next_step_id":"hardware"})
        check(hardware["type"]=="form","hardware settings displayed")
        previous=hass.data[DOMAIN][entry.entry_id]
        saved=await hass.config_entries.options.async_configure(hardware["flow_id"],{
            "piper_base":"http://127.0.0.1:15001",
            "cpu_stt":row.entity_id,
            "hardware_profile":"automatic",
        })
        check(saved["type"]=="create_entry","hardware settings saved: "+str(saved.get("errors",{})))
        await wait_until(lambda: hass.data.get(DOMAIN,{}).get(entry.entry_id) not in (None,previous)
                         and entry.state==ConfigEntryState.LOADED,"hardware settings reload")
        updated=hass.data[DOMAIN][entry.entry_id]
        check(updated.cfg.get("hardware_profile")=="Automatisch","automatic GPU/CPU routing configured")
        check(updated.sources.get("shopping")==todo_id,"hardware settings preserve data-source options")
        menu=await hass.config_entries.options.async_init(entry.entry_id)
        menu=await hass.config_entries.options.async_configure(menu["flow_id"],{"next_step_id":"announcements"})
        check(menu["type"]=="form","optional Alexa announcement settings displayed")
        data=hass.data[DOMAIN][entry.entry_id]  # options reload replaced the per-entry runtime object
        agent=entity(hass,entry,"conversation")
        speech,cid,keep=await converse(hass,agent,"Wie hoch ist die Vorlauftemperatur?")
        check("40" in speech and keep,"flow temperature and follow-up requested")
        speech,_,_=await converse(hass,agent,"Und der Rücklauf?",cid)
        check("36" in speech,"contextual return temperature")
        speech,_,_=await converse(hass,agent,"Wie ist das Wetter aktuell?")
        check("7" in speech,"configured current weather")
        speech,_,_=await converse(hass,agent,"Was haben wir aktuell auf der Bring-Einkaufsliste?")
        check("leer" in speech,"read empty local To-do")
        speech,_,_=await converse(hass,agent,"Setze Milch auf die Einkaufsliste.")
        check("hinzugefügt" in speech,"add real local To-do item")
        speech,_,_=await converse(hass,agent,"Setze Milch auf die Einkaufsliste.")
        check("bereits" in speech,"duplicate protection")
        speech,_,_=await converse(hass,agent,"Was steht auf der Einkaufsliste?")
        check("Milch" in speech,"read persisted item")
        speech,_,_=await converse(hass,agent,"Streiche Milch von der Einkaufsliste.")
        check("entfernt" in speech,"exact item removal")
        text="wir haben welche artikel auf der einkaufsliste"
        data.learning.observe(text)
        check(text in data.learning.snapshot()["candidates"],"optional learning candidate")
        await data.learning.edit("approve",text,"bring_list")
        speech,_,_=await converse(hass,agent,text)
        check("leer" in speech,"approved local alias")
        speech,cid,keep=await converse(hass,agent,"Erinnere mich in zwei Minuten daran, "+MARKER)
        check(keep and MARKER in speech and data.reminders.item is None,"reminder requires confirmation")
        speech,_,_=await converse(hass,agent,"Ja",cid)
        check("gespeichert" in speech and data.reminders.item["message"]==MARKER,"confirmed reminder saved")
        check(dt_util.parse_datetime(data.reminders.item["when"])>dt_util.now(),"future reminder scheduled")
    finally:
        await runner.cleanup()

async def phase_two(hass):
    entries=hass.config_entries.async_entries(DOMAIN)
    check(len(entries)==1,"config entry restored after complete process restart")
    entry=entries[0]
    await entry_loaded(hass,entry)
    check(DOMAIN not in hass.data[frontend.DATA_PANELS],"no TAFA sidebar after restart")
    check(hass.services.has_service(DOMAIN,"room_audio"),"multiroom registered after restart")
    check(hass.data.get(DOMAIN,{}).get("wake_devices_dynamic") is not None,"native wake registry after restart")
    data=hass.data[DOMAIN][entry.entry_id]
    check(data.learning.lookup("wir haben welche artikel auf der einkaufsliste")=="bring_list","approved alias survives restart")
    done=asyncio.Event()
    def notification(_update,notifications):
        if notifications.get("tablet_assist_reminder",{}).get("message")==MARKER:done.set()
    unsubscribe=async_register_callback(hass,notification)
    try:
        check(data.reminders.item is not None,"reminder restored from disk")
        await asyncio.wait_for(done.wait(),timeout=165)
        check(True,"actual scheduled reminder notification delivered")
        await wait_until(lambda: data.reminders.item is None,"delivered reminder cleared from memory")
        check(await data.reminders.store.async_load()=={},"delivered reminder cleared from storage")
    finally:
        unsubscribe()

async def async_setup(hass,config):
    async def run(_event):
        result_path=Path(hass.config.path("ci-result-"+PHASE+".json"))
        try:
            await (phase_one(hass) if PHASE=="one" else phase_two(hass))
            result={"ok":True,"checks":CHECKS}
        except Exception:
            result={"ok":False,"checks":CHECKS,"error":traceback.format_exc()}
            print(result["error"],flush=True)
        # Atomic marker read by the runner after real HA startup.
        def write():
            temp=result_path.with_suffix(".tmp")
            temp.write_text(json.dumps(result,indent=2))
            temp.replace(result_path)
        await hass.async_add_executor_job(write)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED,run)
    return True
