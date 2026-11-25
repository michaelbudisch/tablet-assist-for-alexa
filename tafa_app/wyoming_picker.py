"""Discover registered Wyoming STT providers and save App-owned selections.

The native Supervisor App Configuration editor uses a static options schema.
This authenticated Ingress configuration panel is the dynamic selector.

No guessed hostnames, no full API credentials in UI, and no configuration is
changed merely by listing discovered entities.
"""
import json
import re
import urllib.request

from speech_source import load_options

SUPERVISOR_OPTIONS="http://supervisor/addons/self/options"
STT_PATTERN=re.compile(r"stt\.[a-z0-9_]{1,200}\Z")


def discover_wyoming_stt(token):
    """Return current, enabled Wyoming STT entities from HA's entity registry."""
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    from websockets.sync.client import connect
    with connect("ws://supervisor/core/websocket",open_timeout=6,close_timeout=2) as ws:
        hello=json.loads(ws.recv(timeout=8))
        if hello.get("type")=="auth_required":
            ws.send(json.dumps({"type":"auth","access_token":token}))
            hello=json.loads(ws.recv(timeout=8))
        if hello.get("type")!="auth_ok":
            raise RuntimeError("Home Assistant WebSocket authentication failed")
        ws.send(json.dumps({"id":1,"type":"config/entity_registry/list"}))
        while True:
            response=json.loads(ws.recv(timeout=10))
            if response.get("id")!=1:
                continue
            if not response.get("success"):
                raise RuntimeError("Home Assistant entity registry unavailable")
            records=response.get("result")
            if not isinstance(records,list):
                raise RuntimeError("Invalid Home Assistant entity registry response")
            break
    discovered={}
    for entry in records:
        if (not isinstance(entry,dict) or entry.get("platform")!="wyoming"
                or entry.get("disabled_by")):
            continue
        entity=entry.get("entity_id")
        if not isinstance(entity,str) or not STT_PATTERN.fullmatch(entity):
            continue
        name=entry.get("name") or entry.get("original_name") or ""
        # Only printable, bounded UI data. IDs remain the only values accepted.
        if not isinstance(name,str):
            name=""
        name=" ".join(name.split())[:100]
        discovered[entity]={"id":entity,"name":name}
    return [discovered[key] for key in sorted(discovered)]


def validate_selection(cpu_stt,gpu_stt,available):
    """Never silently change an existing mapping or swap CPU/GPU providers."""
    options={item["id"] for item in available}
    for value in (cpu_stt,gpu_stt):
        if not isinstance(value,str) or (value and value not in options):
            raise ValueError("Select an existing Wyoming STT entity")
    if cpu_stt and cpu_stt==gpu_stt:
        raise ValueError("CPU and GPU require two distinct Wyoming STT entities")
    return {"cpu_stt":cpu_stt,"gpu_stt":gpu_stt}


def save_wyoming_selection(token,cpu_stt,gpu_stt,available):
    """Only update the two STT keys, preserving every unrelated App option.

    Supervisor documents POST /addons/self/options as the persistent options
    endpoint. Values apply when TAFA App next starts; no implicit restart.
    """
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    changes=validate_selection(cpu_stt,gpu_stt,available)
    current=load_options()
    options={**current,**changes}
    data=json.dumps({"options":options},ensure_ascii=False).encode("utf-8")
    request=urllib.request.Request(
        SUPERVISOR_OPTIONS, data=data,method="POST",
        headers={"Authorization":"Bearer "+token,
                 "Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=8) as response:
        if response.status!=200:
            raise RuntimeError("Supervisor option update failed")
        reply=json.loads(response.read(16384))
    if reply.get("result")!="ok":
        raise RuntimeError("Supervisor did not accept the App configuration")
    return changes
