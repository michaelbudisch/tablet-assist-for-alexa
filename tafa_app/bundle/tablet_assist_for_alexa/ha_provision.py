"""Explicit administrator-confirmed provisioning of known private TAFA endpoints.

Called only by the TAFA App through authenticated Home Assistant WebSocket.
Creates/reuses Wyoming and Ollama entries, never deletes entries, never changes
an unrelated configuration, never downloads an LLM model, and never edits the
user's existing Assist pipelines or default conversation agent.
"""
import asyncio
import ipaddress
import re

import aiohttp
import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .app_settings import APP_MANAGED_MARKER
from .const import DOMAIN
from pathlib import Path

COMMAND=DOMAIN+"/provision_manifest"
NETWORKS=(ipaddress.ip_network("10.0.0.0/8"),
          ipaddress.ip_network("172.16.0.0/12"),
          ipaddress.ip_network((3232235520,16)))
TYPES=("gpu_worker","speech_server")


def _private(value):
    try:
        ip=ipaddress.ip_address(value)
    except (TypeError,ValueError) as exc:
        raise ValueError("A private IPv4 host is required") from exc
    if ip.version!=4 or not any(ip in net for net in NETWORKS):
        raise ValueError("Only private LAN addresses are supported")
    return str(ip)


def validate_request(raw):
    if not isinstance(raw,dict) or set(raw)!={"kind","host","services","device_id"}:
        raise ValueError("Malformed TAFA import request")
    if raw["kind"] not in TYPES:
        raise ValueError("Unknown TAFA device kind")
    host=_private(raw["host"])
    device_id=raw["device_id"]
    if not isinstance(device_id,str) or not re.fullmatch(r"[a-f0-9-]{36}",device_id):
        raise ValueError("Invalid device identifier")
    services=raw["services"]
    if not isinstance(services,dict) or set(services)!=(
        {"wyoming_stt","qwen_tts","ollama"} if raw["kind"]=="gpu_worker"
        else {"wyoming_stt","piper","mp3","https_audio"}):
        raise ValueError("Invalid service profile")
    for kind,item in services.items():
        if not isinstance(item,dict) or type(item.get("enabled")) is not bool:
            raise ValueError("Service must declare enabled boolean")
        if kind=="wyoming_stt":
            if item.get("host")!=host or item.get("port")!=10300:
                raise ValueError("Invalid Wyoming endpoint")
        if kind=="ollama":
            if item.get("url")!=f"http://{host}:11434":
                raise ValueError("Invalid Ollama URL")
            model=item.get("model","")
            if not isinstance(model,str) or (model and not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}",model)):
                raise ValueError("Invalid model")
        if kind=="qwen_tts" and item.get("url")!=f"http://{host}:10502":
            raise ValueError("Invalid Qwen URL")
        if kind=="piper" and item.get("url")!=f"http://{host}:5000":
            raise ValueError("Invalid Piper URL")
        if kind=="mp3" and item.get("url")!=f"http://{host}:5001":
            raise ValueError("Invalid MP3 URL")
    return host


def _associated_entry(hass, domain, host, tracked_id, port=None):
    entries=hass.config_entries.async_entries(domain)
    if domain=="wyoming":
        same=[entry for entry in entries if
              entry.data.get("host")==host and entry.data.get("port")==port]
    else:
        url=f"http://{host}:11434"
        same=[entry for entry in entries if entry.data.get("url")==url]
    if len(same)>1:
        raise ValueError("Multiple integration entries match one endpoint")
    if same:
        return same[0],False
    if tracked_id:
        owned=next((entry for entry in entries if entry.entry_id==tracked_id),None)
        if owned is None:
            # A previously imported Wyoming/Ollama entry can have been
            # deleted through HA's normal Devices & Services UI. It is safe
            # to create the configured endpoint again. The new config entry
            # replaces the stale ID in TAFA's stored manifest mapping.
            return None,False
        # Never use a mapped ID belonging to a different domain.
        if owned.domain!=domain:
            raise ValueError("Mismatched integration domain")
        return owned,True
    return None,False


async def _start_flow(hass,domain,data):
    result=await hass.config_entries.flow.async_init(domain,context={"source":"user"})
    if result.get("type")=="form":
        result=await hass.config_entries.flow.async_configure(result["flow_id"],data)
    if result.get("type")=="create_entry":
        return result.get("result")
    if result.get("type")=="abort" and result.get("reason")=="already_configured":
        return None
    raise ValueError(domain+" flow did not finish: "+str(result.get("errors",result.get("type"))))


async def _update_wyoming(hass,entry,host):
    flow=await hass.config_entries.flow.async_init(
        "wyoming",context={"source":"reconfigure","entry_id":entry.entry_id})
    if flow.get("type")!="form":
        raise ValueError("Wyoming reconfigure flow unavailable")
    result=await hass.config_entries.flow.async_configure(
        flow["flow_id"],{"host":host,"port":10300})
    if result.get("type")!="abort" or result.get("reason") not in (
        "reconfigure_successful","reconfigure_successful_unload_failed"):
        raise ValueError("Wyoming reconfigure rejected new host")


async def _installed_models(hass,url):
    session=async_get_clientsession(hass)
    try:
        async with asyncio.timeout(5):
            async with session.get(url+"/api/tags",allow_redirects=False) as response:
                if response.status!=200:
                    return None
                payload=await response.json()
        return {row.get("name") for row in payload.get("models",[])
                if isinstance(row,dict) and isinstance(row.get("name"),str)}
    except (aiohttp.ClientError,TimeoutError,ValueError,TypeError):
        return None


async def provision(hass,manifest,tracked):
    host=validate_request(manifest)
    if not isinstance(tracked,dict) or set(tracked)-{"wyoming_stt","ollama"}:
        raise ValueError("Invalid prior entry mapping")
    for entry_id in tracked.values():
        if not isinstance(entry_id,str) or len(entry_id)>100:
            raise ValueError("Invalid entry reference")
    services=manifest["services"]
    assigned={}
    entity_ids={}
    notices=[]

    if services["wyoming_stt"]["enabled"]:
        entry,change=_associated_entry(hass,"wyoming",host,tracked.get("wyoming_stt"),10300)
        if entry is None:
            created=await _start_flow(hass,"wyoming",{"host":host,"port":10300})
            if created is None:
                entry,_=_associated_entry(hass,"wyoming",host,None,10300)
            else:
                entry=created
        elif change:
            await _update_wyoming(hass,entry,host)
        if entry:
            assigned["wyoming_stt"]=entry.entry_id
            await asyncio.sleep(0)
            registry=er.async_get(hass)
            ids=[row.entity_id for row in er.async_entries_for_config_entry(registry,entry.entry_id)
                 if row.platform=="wyoming" and row.entity_id.startswith("stt.") and not row.disabled_by]
            if len(ids)==1:
                entity_ids["stt"]=ids[0]
            else:
                notices.append("Wyoming created; STT entity pending until HA finishes loading")
        else:
            notices.append("Wyoming registration pending")

    if manifest["kind"]=="gpu_worker" and services["ollama"]["enabled"]:
        endpoint=services["ollama"]["url"]
        models=await _installed_models(hass,endpoint)
        if models is None:
            notices.append("Ollama is not reachable; its integration was left unchanged")
        else:
            entry,change=_associated_entry(hass,"ollama",host,tracked.get("ollama"))
            if entry is None:
                created=await _start_flow(hass,"ollama",{"url":endpoint})
                if created is None:
                    entry,_=_associated_entry(hass,"ollama",host,None)
                else:
                    entry=created
            elif change:
                # HA's current Ollama flow has no host reconfigure step.
                # Only change the previously tracked entry, preserving its
                # other data/options/subentries; verify the new server first.
                hass.config_entries.async_update_entry(
                    entry,data={**entry.data,"url":endpoint})
                await hass.config_entries.async_reload(entry.entry_id)
            if entry:
                assigned["ollama"]=entry.entry_id
                conversations=[sub for sub in entry.subentries.values()
                               if sub.subentry_type=="conversation"]
                chosen=None
                if len(conversations)==1:
                    chosen=conversations[0]
                elif len(conversations)>1:
                    owned=[sub for sub in conversations if sub.title=="TAFA Ollama"]
                    if len(owned)==1:
                        chosen=owned[0]
                    else:
                        notices.append("Multiple Ollama conversation agents; select one in TAFA")
                elif not conversations:
                    model=services["ollama"].get("model") or ""
                    if not model or model not in models:
                        notices.append("Select an installed Ollama model before creating the conversation agent")
                    else:
                        try:
                            flow=await hass.config_entries.subentries.async_init(
                                (entry.entry_id,"conversation"),context={"source":"user"})
                            if flow.get("type")=="form":
                                outcome=await hass.config_entries.subentries.async_configure(
                                    flow["flow_id"],{"name":"TAFA Ollama","model":model})
                                if outcome.get("type") not in ("create_entry","abort"):
                                    notices.append("Ollama conversation agent requires manual review")
                            else:
                                notices.append("Ollama subentry flow unavailable")
                            await asyncio.sleep(0)
                        except (ValueError,RuntimeError,KeyError,TypeError):
                            notices.append("Ollama agent could not be created automatically")
                        conversations=[sub for sub in entry.subentries.values()
                                       if sub.subentry_type=="conversation" and sub.title=="TAFA Ollama"]
                        if len(conversations)==1:
                            chosen=conversations[0]
                if chosen:
                    await asyncio.sleep(0)
                    reg=er.async_get(hass)
                    agents=[row.entity_id for row in er.async_entries_for_config_entry(reg,entry.entry_id)
                            if row.config_subentry_id==chosen.subentry_id
                            and row.platform=="ollama" and row.entity_id.startswith("conversation.")
                            and not row.disabled_by]
                    if len(agents)==1:
                        entity_ids["llm_agent"]=agents[0]
                    else:
                        notices.append("Ollama conversation entity pending; refresh after HA loads it")

    return {"entries":assigned,"entities":entity_ids,"messages":notices}


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"):COMMAND,
    vol.Required("manifest"):dict,
    vol.Required("tracked"):dict,
})
@websocket_api.async_response
async def provision_manifest(hass,connection,msg):
    if not (Path(__file__).parent / APP_MANAGED_MARKER).is_file():
        connection.send_error(msg["id"],"not_managed","TAFA App installation required")
        return
    if len(hass.config_entries.async_entries(DOMAIN))!=1:
        connection.send_error(msg["id"],"not_configured","TAFA backend must be installed")
        return
    try:
        result=await provision(hass,msg["manifest"],msg["tracked"])
    except (ValueError,TypeError,KeyError,RuntimeError,ConnectionError,TimeoutError) as exc:
        # Return a bounded explanation, not just the generic error code.
        # The App displays this in its import preview for troubleshooting.
        connection.send_error(msg["id"],"provision_failed",str(exc)[:180])
        return
    connection.send_result(msg["id"],result)


RESOLVE_COMMAND=DOMAIN+"/resolve_manifest_entities"


def locate_assigned_entities(hass, tracked):
    """Report only entities belonging to previously approved HA config entries."""
    if not isinstance(tracked,dict) or set(tracked)-{"gpu_worker","speech_server"}:
        raise ValueError("Unknown tracked device roles")
    found={}
    pending=[]
    registry=er.async_get(hass)
    for kind, profile in tracked.items():
        if not isinstance(profile,dict) or set(profile)-{"wyoming_stt","ollama","expected"}:
            raise ValueError("Invalid mapped entry profile")
        expected=profile.get("expected") or {}
        if not isinstance(expected,dict) or set(expected)-{"wyoming_stt","ollama"}:
            raise ValueError("Invalid expected services")
        for key in ("wyoming_stt","ollama"):
            entry_id=profile.get(key)
            if not expected.get(key):
                continue
            if not isinstance(entry_id,str) or len(entry_id)>100:
                pending.append(kind+"."+key+": not registered")
                continue
            domain="wyoming" if key=="wyoming_stt" else "ollama"
            entry=hass.config_entries.async_get_entry(entry_id)
            if entry is None or entry.domain!=domain:
                pending.append(kind+"."+key+": unavailable")
                continue
            candidates=[
                row for row in er.async_entries_for_config_entry(registry,entry_id)
                if not row.disabled_by and row.platform==domain
            ]
            if key=="wyoming_stt":
                stts=[row.entity_id for row in candidates if row.entity_id.startswith("stt.")]
                if len(stts)==1:
                    found["gpu_stt" if kind=="gpu_worker" else "cpu_stt"]=stts[0]
                else:
                    pending.append(kind+".wyoming_stt: STT entity pending")
            else:
                conversations=[sub for sub in entry.subentries.values()
                               if sub.subentry_type=="conversation"]
                selected=([sub for sub in conversations if sub.title=="TAFA Ollama"]
                          or conversations if len(conversations)==1 else [])
                if len(selected)!=1:
                    pending.append("gpu_worker.ollama: choose a conversation agent")
                    continue
                entities=[row.entity_id for row in candidates
                          if row.config_subentry_id==selected[0].subentry_id
                          and row.entity_id.startswith("conversation.")]
                if len(entities)==1:
                    found["llm_agent"]=entities[0]
                else:
                    pending.append("gpu_worker.ollama: conversation entity pending")
    return {"entities":found,"pending":pending}


@websocket_api.require_admin
@websocket_api.websocket_command({
    vol.Required("type"):RESOLVE_COMMAND,
    vol.Required("tracked"):dict,
})
@websocket_api.async_response
async def resolve_manifest_entities(hass,connection,msg):
    if not (Path(__file__).parent / APP_MANAGED_MARKER).is_file():
        connection.send_error(msg["id"],"not_managed","TAFA App required")
        return
    try:
        result=locate_assigned_entities(hass,msg["tracked"])
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        connection.send_error(msg["id"],"invalid_mapping",str(exc)[:160])
        return
    connection.send_result(msg["id"],result)
