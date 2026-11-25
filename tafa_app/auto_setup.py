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
