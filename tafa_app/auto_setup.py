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

def configure(piper_base, preferences=None):
    """Create HA's TAFA entry using the App Configuration as the first-run source.

    Existing entries are preserved here. The App subsequently synchronizes
    only its own integration via the authenticated WebSocket command.
    """
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
    if preferences:
        allowed={"hardware_profile", "live_profile", "voice_variant",
                 "mp3_base", "public_audio_base", "mp3_profile",
                 "gpu_base", "chime", "cpu_stt", "gpu_stt",
                 "gpu_stt_host", "llm_agent", "conversation_mode", "rooms_json"}
        fields.update({key:value for key,value in preferences.items() if key in allowed
                       and (value or key not in {"cpu_stt", "gpu_stt", "llm_agent"})})
    try:
        done=call("config/config_entries/flow/"+fid,fields)
        if done.get("type")=="create_entry":
            return "configured"
        if done.get("type")=="abort" and done.get("reason")=="already_configured":
            return "already_configured"
        save_state("needs_attention","Home Assistant integration not yet ready; restart HA after the App update")
        return "needs_attention"
    finally:
        try: call("config/config_entries/flow/"+fid,None,"DELETE")
        except (urllib.error.URLError,RuntimeError,ValueError): pass


def sync_app_configuration(piper_base, preferences):
    """Apply App Configuration to a NEW OR EXISTING App-managed HA entry.

    Supervisor's own token is required internally to authenticate to HA Core;
    no user-supplied API token or public endpoint is involved.
    """
    if not TOKEN:
        raise RuntimeError("Supervisor API access unavailable")
    from websockets.sync.client import connect
    with connect("ws://supervisor/core/websocket", open_timeout=6, close_timeout=2) as ws:
        reply = json.loads(ws.recv(timeout=8))
        if reply.get("type") == "auth_required":
            ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
            reply = json.loads(ws.recv(timeout=8))
        if reply.get("type") != "auth_ok":
            raise RuntimeError("Home Assistant WebSocket authentication failed")
        ws.send(json.dumps({
            "id": 1,
            "type": "tablet_assist_for_alexa/sync_app_configuration",
            "settings": {"piper_base": piper_base, **preferences},
        }))
        while True:
            reply = json.loads(ws.recv(timeout=10))
            if reply.get("id") != 1:
                continue
            if not reply.get("success"):
                reason = reply.get("error", {}).get("code", "not_ready")
                raise RuntimeError("TAFA integration sync failed: " + str(reason))
            return "changed" if reply.get("result", {}).get("changed") else "unchanged"


def ensure_pipeline(external_wyoming=False, configured_stt=""):
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
        if external_wyoming:
            # The HA integration automatically selects the single Wyoming STT
            # provider when App cpu_stt is empty. Avoid falsely declaring
            # native voice ready with zero providers or ambiguous choices.
            wyoming = [
                item.get("entity_id") for item in registry
                if item.get("platform") == "wyoming"
                and str(item.get("entity_id", "")).startswith("stt.")
                and not item.get("disabled_by")
            ]
            if configured_stt:
                if configured_stt not in wyoming:
                    return "waiting_for_external_stt"
            elif len(wyoming) != 1:
                return "waiting_for_external_stt"
        def select(domain,suffix):
            matches=[item.get("entity_id") for item in registry
                     if item.get("platform")=="tablet_assist_for_alexa"
                     and str(item.get("unique_id","")).endswith(suffix)
                     and str(item.get("entity_id","")).startswith(domain+".")
                     and not item.get("disabled_by")]
            return matches[0] if len(matches)==1 else None
        stt=select("stt","_stt_router")
        # Use the GPU-aware provider even when no GPU is configured: it then falls back to Piper.
        tts=select("tts","_stream")
        agent=select("conversation","_conversation_router")
        if not all((stt,tts,agent)):
            return "waiting_for_entities"
        pipelines=rpc("assist_pipeline/pipeline/list")
        existing = next(
            (row for row in (pipelines or {}).get("pipelines",[])
             if str(row.get("name", "")).casefold() == "tafa lokal"), None
        )
        if existing is not None:
            # Do not overwrite user-configured pipelines, but do not claim
            # a broken or half-configured one is voice-ready, either.
            required = ("stt_engine", "tts_engine", "conversation_engine")
            return ("pipeline_exists"
                    if all(existing.get(key) for key in required)
                    else "pipeline_needs_review")
        rpc("assist_pipeline/pipeline/create",
            name="TAFA Lokal",language="de",
            conversation_engine=agent,conversation_language="de",
            stt_engine=stt,stt_language="de",
            tts_engine=tts,tts_language="de",tts_voice=None,
            wake_word_entity=None,wake_word_id=None,
            prefer_local_intents=True)
        return "pipeline_created"


def provision_worker_manifest(manifest, tracked):
    """Provision only administrator-confirmed endpoints through HA's own flow API.

    The HA integration owns safe entity matching and config entries. App process
    sends its manifest over the authenticated Supervisor/Core WebSocket, never
    requests user-supplied API tokens and never opens public worker URLs.
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
        # Old HA Core processes can keep the 0.4.11 Python module loaded
        # after the TAFA App and on-disk integration have been updated.
        # That module rejects a deleted, previously mapped config entry.
        # Retry ONLY that exact server error, and remove only the stale
        # mapping, preserving the approved JSON endpoint and all unrelated
        # Home Assistant config entries. A later successful result persists
        # the newly created config entry through save_record().
        active=dict(tracked)
        retry_keys=[
            key for key in ("wyoming_stt","ollama")
            if key in active and manifest["services"].get(key,{}).get("enabled") is True
        ]
        used_compatibility=False
        for request_id in range(1,len(retry_keys)+2):
            ws.send(json.dumps({
                "id":request_id,"type":"tablet_assist_for_alexa/provision_manifest",
                "manifest": {key:manifest[key] for key in
                             ("kind","host","device_id","services")},
                "tracked":active,
            }))
            reply=None
            for _ in range(8):
                response=json.loads(ws.recv(timeout=35))
                if response.get("id")==request_id:
                    reply=response
                    break
            if reply is None:
                raise RuntimeError("HA provisioning did not answer")
            if reply.get("success"):
                result=reply.get("result",{})
                if used_compatibility and isinstance(result,dict):
                    result.setdefault("messages",[]).append(
                        "Veraltete Wyoming-/Ollama-Zuordnung wurde beim JSON-Import repariert. "
                        "/ Deleted integration mapping repaired during JSON import.")
                return result
            error=reply.get("error") or {}
            code=str(error.get("code","unknown"))
            if code in ("unknown_command","not_found"):
                raise RuntimeError(
                    "TAFA HA backend not loaded yet. Restart Home Assistant Core once, "
                    "then retry JSON import / TAFA-Backend noch nicht geladen. "
                    "Home Assistant Core einmal neu starten.")
            detail=" ".join(str(error.get("message") or "").split())[:150]
            if (code=="provision_failed"
                    and detail=="Previously mapped integration missing; review first"
                    and retry_keys):
                active.pop(retry_keys.pop(0),None)
                used_compatibility=True
                continue
            raise RuntimeError("TAFA HA provisioning unavailable: "+code+
                               (" — "+detail if detail else ""))
        raise RuntimeError("TAFA HA provisioning retry limit exceeded")



def resolve_import_entities(tracked):
    """Read back Home Assistant entities for previously confirmed device entries.

    This never adds or edits HA config entries. It is safe to retry while
    Wyoming/Ollama entity registration finishes in Home Assistant.
    """
    if not TOKEN:
        raise RuntimeError("Supervisor API access unavailable")
    from websockets.sync.client import connect
    with connect("ws://supervisor/core/websocket",open_timeout=4,close_timeout=2) as ws:
        first=json.loads(ws.recv(timeout=5))
        if first.get("type")=="auth_required":
            ws.send(json.dumps({"type":"auth","access_token":TOKEN}))
            first=json.loads(ws.recv(timeout=5))
        if first.get("type")!="auth_ok":
            raise RuntimeError("Home Assistant authentication unavailable")
        ws.send(json.dumps({"id":1,"type":"tablet_assist_for_alexa/resolve_manifest_entities",
                            "tracked":tracked}))
        for _ in range(10):
            reply=json.loads(ws.recv(timeout=8))
            if reply.get("id")!=1:
                continue
            if not reply.get("success"):
                raise RuntimeError("TAFA backend entity resolution unavailable: "+
                                   str((reply.get("error") or {}).get("code","unknown")))
            result=reply.get("result")
            if not isinstance(result,dict):
                raise RuntimeError("Invalid entity resolution response")
            return result
    raise RuntimeError("HA did not return entity assignments")


def inspect_tafa_pipeline():
    """Read-only readiness check: no pipeline creation or default changes."""
    if not TOKEN:
        return {"status":"not_available","detail":"Supervisor authentication unavailable"}
    from websockets.sync.client import connect
    try:
        with connect("ws://supervisor/core/websocket",open_timeout=3,close_timeout=2) as ws:
            first=json.loads(ws.recv(timeout=4))
            if first.get("type")=="auth_required":
                ws.send(json.dumps({"type":"auth","access_token":TOKEN}))
                first=json.loads(ws.recv(timeout=4))
            if first.get("type")!="auth_ok":
                return {"status":"not_available","detail":"HA authentication unavailable"}
            def query(identifier,command):
                ws.send(json.dumps({"id":identifier,"type":command}))
                for _ in range(8):
                    reply=json.loads(ws.recv(timeout=4))
                    if reply.get("id")==identifier:
                        return reply.get("result") if reply.get("success") else None
                return None
            data=query(1,"assist_pipeline/pipeline/list")
            registry=query(2,"config/entity_registry/list")
            if not isinstance(data,dict) or not isinstance(registry,list):
                return {"status":"not_available","detail":"HA Assist API not ready"}
            pipeline=next((p for p in (data.get("pipelines") or [])
                          if isinstance(p,dict) and str(p.get("name","")).casefold()=="tafa lokal"),None)
            if pipeline is None:
                return {"status":"waiting","detail":"TAFA Lokal is being configured"}
            required={"stt_engine":"_stt_router","tts_engine":"_stream",
                      "conversation_engine":"_conversation_router"}
            found={}
            for field,unique_suffix in required.items():
                candidates=[item.get("entity_id") for item in registry
                            if item.get("platform")=="tablet_assist_for_alexa"
                            and str(item.get("unique_id","")).endswith(unique_suffix)
                            and not item.get("disabled_by")]
                found[field]=candidates[0] if len(candidates)==1 else None
            if not all(found.values()):
                return {"status":"waiting","detail":"TAFA Assist entities still registering"}
            if any(pipeline.get(field)!=entity for field,entity in found.items()):
                return {"status":"needs_review","detail":"Existing pipeline differs from TAFA router"}
            return {"status":"ready","detail":"TAFA Lokal pipeline and all three routers are registered"}
    except (OSError,TimeoutError,ValueError,TypeError,KeyError):
        return {"status":"not_available","detail":"HA Assist API temporarily unavailable"}
