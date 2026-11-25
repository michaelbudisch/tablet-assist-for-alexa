"""Optional automatic Home Assistant config entry flow for the bundled CPU service."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

STATE = Path("/data/tafa_ha_state.json")
BASE = "http://supervisor/core/api/"
TOKEN = os.environ.get("SUPERVISOR_TOKEN","")

def save_state(status,detail=""):
    STATE.write_text(json.dumps({"status":status,"detail":detail[:150]}))

def call(path,data=None,method="POST"):
    if not TOKEN:
        raise RuntimeError("Supervisor API access unavailable")
    body=json.dumps(data).encode() if data is not None else None
    req=urllib.request.Request(BASE+path,data=body,
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"},
        method=method)
    with urllib.request.urlopen(req,timeout=8) as response:
        return json.loads(response.read(65536).decode())

def configure(piper_base):
    """Use HA's documented config flow REST API. Never modify .storage directly."""
    flow=call("config/config_entries/flow",{"handler":"tablet_assist_for_alexa"})
    if flow.get("type")=="abort":
        return "already_configured"
    if flow.get("type")!="form" or not flow.get("flow_id"):
        raise RuntimeError("HA configuration flow not available")
    fid=flow["flow_id"]
    fields={"piper_base":piper_base,"hardware_profile":"automatic",
            "live_profile":"natural","voice_variant":"default",
            "conversation_mode":"intelligent","mp3_profile":"natural",
            "rooms_json":"{}","chime":False}
    try:
        done=call("config/config_entries/flow/"+fid,fields)
        if done.get("type")=="create_entry":
            return "configured"
        if done.get("type")=="abort" and done.get("reason")=="already_configured":
            return "already_configured"
        save_state("needs_attention","HA rejected automatic config; configure TAFA in Devices & services")
        return "needs_attention"
    finally:
        try: call("config/config_entries/flow/"+fid,None,"DELETE")
        except (urllib.error.URLError,RuntimeError,ValueError): pass


def ensure_pipeline():
    """Create one TAFA Assist pipeline only after all three HA entities exist.

    Never replace the preferred pipeline or alter another device's settings.
    """
    if not TOKEN:
        raise RuntimeError("Supervisor API access unavailable")
    from websockets.sync.client import connect
    with connect("ws://supervisor/core/websocket",open_timeout=6,close_timeout=2) as ws:
        first=json.loads(ws.recv(timeout=8))
        if first.get("type")=="auth_required":
            ws.send(json.dumps({"type":"auth","access_token":TOKEN}))
            first=json.loads(ws.recv(timeout=8))
        if first.get("type")!="auth_ok":
            raise RuntimeError("Home Assistant WebSocket authentication failed")
        counter=0
        def rpc(kind,**arguments):
            nonlocal counter
            counter+=1
            ws.send(json.dumps({"id":counter,"type":kind,**arguments}))
            while True:
                reply=json.loads(ws.recv(timeout=10))
                if reply.get("id")==counter:
                    if not reply.get("success"):
                        raise RuntimeError("HA API rejected "+kind)
                    return reply.get("result")
        registry=rpc("config/entity_registry/list")
        def select(domain,suffix):
            matches=[item.get("entity_id") for item in registry
                     if item.get("platform")=="tablet_assist_for_alexa"
                     and str(item.get("unique_id","")).endswith(suffix)
                     and str(item.get("entity_id","")).startswith(domain+".")
                     and not item.get("disabled_by")]
            return matches[0] if len(matches)==1 else None
        stt=select("stt","_stt_router")
        tts=select("tts","_piper")
        agent=select("conversation","_conversation_router")
        if not all((stt,tts,agent)):
            return "waiting_for_entities"
        pipelines=rpc("assist_pipeline/pipeline/list")
        if any(str(row.get("name","")).casefold()=="tafa lokal"
               for row in (pipelines or {}).get("pipelines",[])):
            return "pipeline_exists"
        rpc("assist_pipeline/pipeline/create",
            name="TAFA Lokal",language="de",
            conversation_engine=agent,conversation_language="de",
            stt_engine=stt,stt_language="de",
            tts_engine=tts,tts_language="de",tts_voice=None,
            prefer_local_intents=True)
        return "pipeline_created"
