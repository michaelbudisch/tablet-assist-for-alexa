"""TAFA Home Assistant App: administrator-only Ingress Control Center.

Installs one unified HA integration, starts private CPU speech and offers a
read-only status page. No dashboard assets, secrets or household data shipped.
"""
import html
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs

from auto_setup import configure, sync_app_configuration, ensure_pipeline, save_state, STATE as SETUP_STATE
from installer import bootstrap, status
from speech_source import (choose as choose_speech_source,
                           piper_ready as external_piper_ready,
                           setup_settings, setup_settings_values, connection_status)
from model_store import inventory as local_model_inventory, remove_local_models
from wyoming_picker import discover_wyoming_stt, save_wyoming_selection
from settings_ui import render_settings_form, save_settings_form, render_connection_form, save_connection_form
from endpoint_checks import assess_endpoints, recent_stt_backend
from connection_probes import probe_connection, ADDRESS_FIELDS
from control_center_view import render_dashboard
from voice_test_view import render_voice_panel, public_device_snapshot
from voice_test import run_voice, voice_status, load_audio, VoiceTestError, MAX_AUDIO
from device_center import read_device_data, render_device_center, update_device, set_native_microphone_mode, pair_device, create_room, set_room_camera, remove_device, unpair_device, delete_room
from import_manifest import preview as preview_import, consume as consume_import, proposed_options, reconcile_imported_stt, load_records, save_record, render_panel
from auto_setup import provision_worker_manifest, resolve_import_entities, inspect_tafa_pipeline
from settings_ui import save_app_changes
from speech_source import load_options

LOG=logging.getLogger("tafa.app")
CONFIG=Path("/homeassistant")
BUNDLE=Path(__file__).parent/"bundle"
CSRF=secrets.token_urlsafe(32)
REPO="https://github.com/michaelbudisch/tablet-assist-for-alexa"
TOKEN=os.environ.get("SUPERVISOR_TOKEN","")
STATUS_URL="http://127.0.0.1:5000/status"
SETUP_LOCK=threading.Lock()
CPU_LOCK=threading.Lock()
FINALIZER_LOCK=threading.Lock()
SETUP_GENERATION=0
CPU_THREAD=None
FINALIZER_THREAD=None
APP_VERSION="0.3.48"

def _json_url(url,token="",timeout=2):
    hdr={"Authorization":"Bearer "+token} if token else {}
    with urllib.request.urlopen(urllib.request.Request(url,headers=hdr),timeout=timeout) as res:
        return json.loads(res.read(65536).decode("utf-8"))

def _internal_address():
    hostname=None
    if TOKEN:
        try:
            info=_json_url("http://supervisor/addons/self/info",TOKEN)
            hostname=info.get("data",{}).get("hostname")
        except (OSError,ValueError,KeyError,TypeError):
            pass
    if isinstance(hostname,str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{1,70}",hostname):
        return "http://"+hostname+":5000"
    ip=ipaddress.ip_address(socket.gethostbyname(socket.gethostname()))
    if not ip.is_private or ip.is_loopback:
        raise RuntimeError("Cannot identify private HA app network address")
    return "http://"+str(ip)+":5000"

def publish_service_address(address):
    root=CONFIG/".tafa"
    root.mkdir(mode=0o700,exist_ok=True)
    path=root/"service.json"
    candidate=root/"service.json.tmp"
    candidate.write_text(json.dumps({"schema":1,"piper_base":address}),encoding="utf-8")
    os.chmod(candidate,0o600)
    candidate.replace(path)

def speech_status():
    try:
        return _json_url(STATUS_URL,timeout=0.8)
    except (OSError,ValueError):
        return {"piper_ready":False,"whisper_ready":False,
                "piper_error":"Service offline","whisper_error":"Service offline"}

def retry_models():
    """Ask the internal CPU worker to retry failed model initialization."""
    req=urllib.request.Request("http://127.0.0.1:5000/retry",data=b"{}",method="POST",
                               headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=3) as response:
        return json.loads(response.read(2048).decode("utf-8")).get("accepted",False)

def setup_status():
    try:
        return json.loads(SETUP_STATE.read_text())
    except (OSError,ValueError):
        return {"status":"pending","detail":""}

def autoconfigure(address, mode="local"):
    # Reattempt after HA Core restarts and discovers newly installed files.
    generation=SETUP_GENERATION
    while True:
        if generation!=SETUP_GENERATION:
            return
        try:
            if mode == "external":
                if not external_piper_ready(address):
                    save_state("waiting_for_external_piper", "Check Proxmox Piper /health on the private LAN")
                    time.sleep(20)
                    continue
                settings = setup_settings()
                # Always install and synchronize the HA integration first.
                # Missing STT must NOT prevent Device Bridge pairing or TTS.
                outcome=configure(address,settings)
                if outcome in ("configured", "already_configured"):
                    # App Configuration is authoritative even for already-existing
                    # HA entries. Do not require Devices & services options.
                    sync_app_configuration(address, settings)
                    # A single Wyoming STT entity can be automatically chosen by
                    # TAFA's HA settings sync even if App cpu_stt was left blank.
                    # Validate providers after sync, not raw App options.
                    pipeline = ensure_pipeline(
                        external_wyoming=True,
                        configured_stt=(settings.get("cpu_stt") or
                                        settings.get("gpu_stt") or ""))
                    if pipeline in ("pipeline_created", "pipeline_exists"):
                        save_state("external_ready",
                                   "App settings synchronized; " + pipeline +
                                   ". TAFA Lokal Assist pipeline available.")
                        LOG.info("TAFA external speech / Assist pipeline ready: %s", pipeline)
                        return
                    if pipeline == "waiting_for_external_stt":
                        save_state("waiting_for_external_stt",
                                   "Connect Wyoming Whisper STT in HA first. TAFA can "
                                   "auto-select one Wyoming provider, or select its entity "
                                   "explicitly as cpu_stt under TAFA App Configuration.")
                    elif pipeline == "waiting_for_entities":
                        save_state("waiting_for_entities",
                                   "External Proxmox: add Wyoming STT in Home Assistant, "
                                   "select its entity in TAFA App Configuration "
                                   "(cpu_stt), and restart HA if integration was just installed.")
                    elif pipeline == "pipeline_needs_review":
                        save_state("pipeline_needs_review",
                                   "Existing TAFA Lokal pipeline has missing Assist stages; "
                                   "open HA Settings -> Voice assistants and complete it.")
                    else:
                        save_state("waiting_for_pipeline", "Assist pipeline status: " + pipeline)
                    time.sleep(20)
                    continue
                save_state(outcome)
                time.sleep(20)
                continue
            speech=speech_status()
            if not (speech.get("piper_ready") and speech.get("whisper_ready")):
                failed = "piper" if not speech.get("piper_ready") else "whisper"
                phase=str(speech.get(failed+"_phase","initializing"))
                error=speech.get(failed+"_error","") if phase=="error" else ""
                save_state("waiting_for_speech",(failed+" "+(str(error) if error else phase))[:150])
                time.sleep(20)
                continue
            if speech.get("piper_ready") and speech.get("whisper_ready"):
                outcome=configure(address,setup_settings())
                save_state(outcome)
                if outcome in ("configured","already_configured"):
                    sync_app_configuration(address, setup_settings())
                    pipeline=ensure_pipeline()
                    save_state(pipeline)
                    if pipeline in ("pipeline_created","pipeline_exists"):
                        LOG.info("TAFA Assist pipeline ready: %s",pipeline)
                        return
        except (urllib.error.URLError,TimeoutError,ValueError,RuntimeError) as exc:
            save_state("waiting_for_home_assistant",type(exc).__name__)
        time.sleep(20)

def monitor_speech():
    """Restart an exited speech worker while keeping the Ingress UI responsive."""
    worker = str(Path(__file__).parent / "speech_proxy.py")
    while True:
        try:
            if choose_speech_source()[0] != "local":
                return
            child = subprocess.Popen([sys.executable,worker])
            # End the local speech subprocess when imported Proxmox mode takes
            # over. A service does not keep downloading models after switching.
            while child.poll() is None:
                try:
                    active=choose_speech_source()[0] == "local"
                except (OSError,ValueError):
                    active=False
                if not active:
                    child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=5)
                    LOG.info("Bundled CPU speech stopped after mode switch")
                    return
                time.sleep(2)
            LOG.error("CPU speech process exited with code %s; restarting in 10 s",child.returncode)
        except OSError as exc:
            LOG.error("CPU speech process could not start: %s",type(exc).__name__)
        time.sleep(10)

def _cpu_monitor():
    global CPU_THREAD
    with CPU_LOCK:
        if CPU_THREAD and CPU_THREAD.is_alive():
            return
        CPU_THREAD=threading.Thread(target=monitor_speech,daemon=True)
        CPU_THREAD.start()


def _launch_autoconfigure(address,mode):
    global SETUP_GENERATION
    with SETUP_LOCK:
        SETUP_GENERATION+=1
        threading.Thread(target=autoconfigure,args=(address,mode),daemon=True).start()


def _tracked_profiles():
    """Resolve only the import-approved Home Assistant device mappings."""
    tracked={}
    duplicates=set()
    for device in load_records().values():
        if not isinstance(device,dict):
            continue
        kind=device.get("kind")
        if kind not in ("gpu_worker","speech_server"):
            continue
        if kind in tracked:
            duplicates.add(kind)
            continue
        entries=device.get("entries") or {}
        expected=device.get("expected") or {}
        if not isinstance(entries,dict) or not isinstance(expected,dict):
            continue
        tracked[kind]={
            **{key:entry for key,entry in entries.items()
               if key in ("wyoming_stt","ollama") and isinstance(entry,str)},
            "expected":{key:expected.get(key) is True for key in ("wyoming_stt","ollama")},
        }
    for kind in duplicates:
        tracked.pop(kind,None)
    return tracked


def _complete_imports():
    """Resume confirmed provisioning after HA reload, then map delayed entities."""
    while True:
        records=load_records()
        if not records:
            return
        still_pending=False
        for rec in records.values():
            if not isinstance(rec,dict) or not rec.get("provision_pending"):
                continue
            manifest=rec.get("manifest")
            if not isinstance(manifest,dict):
                continue
            try:
                results=provision_worker_manifest(manifest,rec.get("entries") or {})
                assigned=results.get("entries") or {}
                entities=results.get("entities") or {}
                changes={}
                role="gpu_stt" if manifest["kind"]=="gpu_worker" else "cpu_stt"
                if isinstance(entities.get("stt"),str):
                    changes[role]=entities["stt"]
                if manifest["kind"]=="gpu_worker" and isinstance(entities.get("llm_agent"),str):
                    changes["llm_agent"]=entities["llm_agent"]
                if changes:
                    current=load_options()
                    changes=reconcile_imported_stt(current,changes,manifest["kind"])
                    save_app_changes(TOKEN,changes,import_kind=manifest["kind"])
                save_record(manifest,assigned)
            except (OSError,RuntimeError,ValueError,TimeoutError) as exc:
                still_pending=True
                LOG.warning("TAFA approved HA setup pending: %s",str(exc)[:110])
        if still_pending:
            save_state("awaiting_core_restart",
                       "HA backend not yet available; approved JSON is saved for automatic resume")
            time.sleep(10)
            continue
        mappings=_tracked_profiles()
        if not mappings:
            return
        try:
            outcome=resolve_import_entities(mappings)
            assigned=outcome.get("entities",{})
            pending=outcome.get("pending",[])
            if not isinstance(assigned,dict) or not isinstance(pending,list):
                raise RuntimeError("Unexpected HA entity mapping")
            current=load_options()
            changes={k:v for k,v in assigned.items()
                     if k in ("gpu_stt","cpu_stt","llm_agent")
                     and isinstance(v,str) and current.get(k)!=v}
            if changes or (current.get("cpu_stt") and current.get("cpu_stt")==current.get("gpu_stt")):
                if changes.get("gpu_stt") and changes["gpu_stt"]==changes.get("cpu_stt"):
                    LOG.warning("CPU and GPU manifests resolved to the same Wyoming STT; "
                                "preferring the verified GPU mapping")
                    changes.pop("cpu_stt",None)
                preferred_kind=("gpu_worker" if "gpu_stt" in changes or
                                ("cpu_stt" not in changes and "gpu_worker" in mappings)
                                else "speech_server")
                changes=reconcile_imported_stt(current,changes,preferred_kind)
                save_app_changes(TOKEN,changes,import_kind=preferred_kind)
                mode,base=choose_speech_source()
                if mode!="setup":
                    service=_internal_address() if mode=="local" else base
                    sync_app_configuration(service,setup_settings())
            if not pending:
                LOG.info("TAFA imported entity mappings complete")
                return
            LOG.info("TAFA waiting for imported entities: %s",", ".join(str(p)[:70] for p in pending))
        except (OSError,ValueError,RuntimeError,TimeoutError) as exc:
            LOG.warning("TAFA entity mapping retry: %s",str(exc)[:120])
        time.sleep(10)


def _start_import_finalizer():
    global FINALIZER_THREAD
    if not load_records():
        return
    with FINALIZER_LOCK:
        if FINALIZER_THREAD and FINALIZER_THREAD.is_alive():
            return
        FINALIZER_THREAD=threading.Thread(target=_complete_imports,daemon=True)
        FINALIZER_THREAD.start()


def restart_home_assistant_core():
    """Disruptive HA restart, invoked only with an explicit import checkbox/button."""
    if not TOKEN:
        raise RuntimeError("Supervisor API unavailable")
    request=urllib.request.Request(
        "http://supervisor/core/restart",data=b"{}",method="POST",
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json"})
    with urllib.request.urlopen(request,timeout=8) as response:
        if response.status not in (200,202):
            raise RuntimeError("Supervisor refused Home Assistant Core restart")
        raw=response.read(16384)
        if raw:
            result=json.loads(raw.decode("utf-8"))
            if not isinstance(result,dict) or result.get("result")!="ok":
                raise RuntimeError("Supervisor did not accept Home Assistant Core restart")


def activate_configured_services():
    """Apply confirmed App options immediately; no blind extra restart."""
    mode,external_base=choose_speech_source()
    if mode=="setup":
        save_state("awaiting_import","Import GPU/Proxmox JSON or select the built-in CPU server")
        return
    if mode=="local":
        _cpu_monitor()
        address=_internal_address()
    else:
        address=external_base
    publish_service_address(address)
    _launch_autoconfigure(address,mode)
    _start_import_finalizer()


def startup():
    try:
        added=bootstrap(CONFIG,BUNDLE)
        if added: LOG.info("Unified TAFA backend staged. Home Assistant must restart to discover it.")
        else: LOG.info("Existing TAFA installation preserved.")
    except (OSError,ValueError,SyntaxError) as exc:
        LOG.error("Backend installation could not complete: %s",type(exc).__name__)
    try:
        mode, external_base=choose_speech_source()
        if mode=="setup":
            save_state("awaiting_import","Select GPU/Proxmox JSON before starting CPU model downloads")
            LOG.info("TAFA first-run setup: awaiting confirmed JSON, CPU model downloads disabled")
        else:
            activate_configured_services()
            LOG.info("TAFA speech mode: %s",mode)

    except (OSError,RuntimeError,ValueError) as exc:
        LOG.error("Automatic HA setup unavailable: %s",type(exc).__name__)
        save_state("needs_attention",str(exc)[:150])

def display(message="",lang="de",default_tab="overview",review=None):
    en=lang=="en"
    t=lambda de,eng:eng if en else de
    state=status(CONFIG)
    try:
        mode, external_base = choose_speech_source()
        preferences=setup_settings()
        source_error=""
    except (OSError, ValueError) as exc:
        mode, external_base, source_error = "invalid", "", str(exc)
        preferences={"gpu_base":"","mp3_base":"","hardware_profile":"cpu"}
    if mode == "local":
        runtime=speech_status()
    elif mode == "external":
        runtime={"piper_ready":external_piper_ready(external_base),
                 "whisper_ready":False, "piper_phase":"external",
                 "whisper_phase":"external"}
    else:
        runtime={"piper_ready":False,"whisper_ready":False,
                 "piper_phase":"error","piper_error":source_error,
                 "whisper_phase":"external"}
    setup=setup_status()
    if any(isinstance(rec,dict) and rec.get("provision_pending")
           for rec in load_records().values()):
        setup={"status":"awaiting_core_restart",
               "detail":"Approved JSON queued until HA has loaded the new TAFA backend"}
    if mode=="setup":
        runtime={"piper_ready":False,"whisper_ready":False,
                 "piper_phase":"setup","whisper_phase":"setup"}
    links=connection_status(preferences, runtime.get("piper_ready") is True)
    pipeline=inspect_tafa_pipeline()
    cache=local_model_inventory()
    translations={
      "not_configured":t("Nicht eingerichtet","Not configured"),
      "offline":t("Nicht erreichbar","Unreachable"),
      "busy":t("Beschäftigt – Piper übernehmen","Busy – use Piper"),
      "ready":t("Bereit","Ready"),
      "not_ready":t("Erreichbar, aber nicht bereit","Reachable, not ready"),
      "qwen":t("Qwen bevorzugt, Piper bleibt Reserve","Qwen preferred, Piper available as reserve"),
      "piper":t("Piper-Fallback verfügbar","Piper fallback available"),
      "none":t("Keine einsatzbereite Sprachausgabe","No ready speech engine")}
    def pretty_size(count):
        return f"{count / 1048576:.1f} MiB"
    cache_info=(t("TAFA-Modelldaten","TAFA model cache")+": Piper "+pretty_size(cache["piper_bytes"])+
                " · Whisper "+pretty_size(cache["whisper_bytes"]))
    def model_state(prefix):
        if runtime.get(prefix+"_ready"):
            return t("Bereit","Ready")
        phase=str(runtime.get(prefix+"_phase","initializing"))
        stages={"loading":t("Modell wird geladen","Loading model"),
                "downloading":t("Modell wird heruntergeladen","Downloading model"),
                "initializing":t("Startet","Starting"),
                "error":t("Fehler","Error")}
        detail=str(runtime.get(prefix+"_error",""))[:180] if phase=="error" else ""
        return stages.get(phase,t("Noch nicht bereit","Not ready")) + (": "+detail if detail else "")
    cards=[
      (t("Home-Assistant-Backend","Home Assistant backend"),state.get("tablet_assist_for_alexa","not installed")),
      (t("Piper · extern (Proxmox)","Piper · external (Proxmox)") if mode == "external" else "Piper · TTS",
       model_state("piper")),
      ("Whisper · STT", t("Über Wyoming in HA einrichten","Configure Wyoming in HA")
       if mode == "external" else model_state("whisper")),
      (t("HA-Einrichtung","HA setup"),setup.get("status","pending")),
      (t("GPU-Worker / Qwen","GPU worker / Qwen"),
       translations.get(links["gpu"],links["gpu"])+
       (" · v"+links["gpu_version"] if links["gpu_version"] else "")),
      (t("Lokale KI · Gesprächsassistent","Local AI · conversation agent"),
       t("Kein KI-Agent ausgewählt; Ollama als HA-Integration hinzufügen und unter TAFA Control Center → Einstellungen als KI-Agent auswählen",
         "No AI agent selected; add Ollama as an HA integration, then select it in TAFA Control Center → Settings → AI agent")
       if not preferences.get("llm_agent") else
       t("Ausgewählt (nicht live getestet): ","Selected (not live-tested): ")+preferences["llm_agent"]),
      (t("Piper-Fallback","Piper fallback"),
       translations.get(links["piper"],links["piper"])),
      (t("Sprachweg laut App-Einstellung","Expected App speech route"),
       translations.get(links["route"],links["route"])),
      (t("Alexa MP3-Generator","Alexa MP3 generator"),
       translations.get(links["mp3"],links["mp3"]))
    ]
    panels="".join('<div class="tile"><strong>'+html.escape(a)+'</strong><span>'+html.escape(str(b))+'</span></div>' for a,b in cards)
    note=t("Neue Komponenten werden beim App-Start eingebunden. Home Assistant muss danach einmal neu gestartet werden.",
      "New components are staged at app startup. Home Assistant needs one restart afterwards.")
    install=t("Backend erneut prüfen","Check backend installation")
    retry=t("Sprachmodelle erneut laden","Retry speech models")
    retry_button=(f'<button type="submit" name="action" value="models">{retry}</button>'
                  if mode == "local" else "")
    has_cache=cache["piper_bytes"] > 0 or cache["whisper_bytes"] > 0
    remove_button=(
        f'<form action="./" method="post"><input type="hidden" name="csrf" value="{CSRF}">'
        f'<input type="hidden" name="lang" value="{lang}"><input type="hidden" name="tab" value="maintenance">'
        f'<label>{t("Zur Bestätigung ENTFERNEN eingeben","Type ENTFERNEN to confirm")}'
        f'<input name="confirmation" type="text" maxlength="10" required pattern="ENTFERNEN" autocomplete="off"></label>'
        f'<button type="submit" name="action" value="cleanup">{t("TAFA-Sprachmodelle löschen","Delete TAFA speech models")}</button>'
        f'</form>' if mode == "external" and has_cache else "")
    # Home Assistant's native App options schema has no dynamic entity picker.
    # This admin-only Ingress UI reads the HA registry without changing it.
    current_cpu=str(preferences.get("cpu_stt","") or "")
    current_gpu=str(preferences.get("gpu_stt","") or "")
    try:
        wyoming_entries=discover_wyoming_stt(TOKEN)
        wyoming_error=""
    except Exception:
        wyoming_entries=[]
        wyoming_error=t("Wyoming-Entitaeten momentan nicht abrufbar.",
                        "Wyoming entities temporarily unavailable.")
    def stt_options(selected):
        choices=['<option value=""'+(' selected' if not selected else '')+
                 '>'+t("Keine / deaktiviert","None / disabled")+'</option>']
        available={item["id"] for item in wyoming_entries}
        if selected and selected not in available:
            choices.append('<option disabled selected value="'+html.escape(selected,quote=True)+'">'+
                           html.escape(selected)+' ('+t("nicht gefunden","not found")+')</option>')
        for item in wyoming_entries:
            name=item["name"] or item["id"]
            label=name+(" · "+item["id"] if name!=item["id"] else "")
            choices.append('<option value="'+html.escape(item["id"],quote=True)+'"'+
                           (' selected' if selected==item["id"] else '')+'>'+
                           html.escape(label)+'</option>')
        return "".join(choices)
    picker_note=wyoming_error or (t("Keine Wyoming-STT-Entitaeten gefunden. Erst Wyoming Protocol in HA installieren.",
                              "No Wyoming STT entities found. Install Wyoming Protocol in HA first.")
                           if not wyoming_entries else t("Erkannte Entitaeten: ","Discovered entities: ")+str(len(wyoming_entries)))
    # The Control Center edits the same persisted Supervisor options as the
    # advanced HA App Configuration screen (never a second settings store).
    checks=assess_endpoints({**load_options(),**preferences},mode,runtime,links,wyoming_entries)
    latest=recent_stt_backend(TOKEN) if TOKEN else None
    picker=render_settings_form({**load_options(),**preferences},wyoming_entries,lang,CSRF,picker_note,checks=checks,latest=latest)
    import_panel=render_panel(lang,CSRF,review=review)
    connection_panel=render_connection_form({**load_options(),**preferences},lang,CSRF,
                                            checks=checks,wyoming=wyoming_entries,
                                            wyoming_note=picker_note,latest=latest)
    device_state = read_device_data()
    if device_state.get("error") or device_state.get("room_error"):
        LOG.warning("TAFA device endpoints: wake=%s room=%s",
                    device_state.get("error") or "ok",
                    device_state.get("room_error") or "ok")
    devices_panel=render_device_center(lang,CSRF,device_state)
    voice_panel=render_voice_panel(lang,CSRF,device_state)
    return render_dashboard(
        pipeline=pipeline,
        lang=lang, version=APP_VERSION, default_tab=default_tab,
        message=message, repo=REPO, csrf=CSRF,
        cards=cards, picker=picker, connection_panel=connection_panel, import_panel=import_panel, devices_panel=devices_panel, voice_panel=voice_panel, checks=checks,
        options={**load_options(), **preferences}, setup=setup,
        links=links, latest=latest, cache_info=cache_info,
        note=note, install=install, retry_button=retry_button,
        remove_button=remove_button, mode=mode)

class Handler(BaseHTTPRequestHandler):
    def allowed(self):
        # Only the HA Supervisor ingress proxy or container-local health probes.
        return self.client_address[0] in ("172.30.32.2","127.0.0.1","::1")
    def respond(self,body,status_code=200):
        content=body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self'; media-src 'self'; img-src 'self'; form-action 'self'; frame-ancestors 'self'; base-uri 'none'")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    def respond_json(self,payload,status_code=200):
        body=json.dumps(payload,separators=(",",":")).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'none'; frame-ancestors 'none'")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self.allowed():return self.send_error(403)
        path=urlsplit(self.path).path
        assets={"/assets/control-center.css":("control_center.css","text/css; charset=utf-8"),
                "/assets/control-center.js":("control_center.js","text/javascript; charset=utf-8"),
                "/assets/voice-test.js":("voice-test.js","text/javascript; charset=utf-8"),
                "/assets/brand.svg":("brand.svg","image/svg+xml")}
        if path in assets:
            filename,mimetype=assets[path]
            content=(Path(__file__).parent/filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type",mimetype)
            self.send_header("Content-Length",str(len(content)))
            self.send_header("Cache-Control","public, max-age=300")
            self.send_header("X-Content-Type-Options","nosniff")
            self.end_headers()
            self.wfile.write(content)
            return
        if path.startswith("/voice/audio/"):
            identifier=path[len("/voice/audio/"):]
            try:
                data,mime=load_audio(TOKEN,identifier)
            except (OSError,ValueError,RuntimeError,TimeoutError):
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type",mime)
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path not in ("/",""):
            return self.send_error(404)
        query=parse_qs(urlsplit(self.path).query)
        lang="en" if query.get("lang")==["en"] else "de"
        tab=query.get("tab",["overview"])[0]
        self.respond(display(lang=lang,default_tab=tab))
    def do_POST(self):
        if not self.allowed():return self.send_error(403)
        length=self.headers.get("Content-Length")
        if urlsplit(getattr(self,"path","/")).path == "/voice/run":
            if (self.headers.get_content_type()!="application/octet-stream"
                    or not length or not length.isdigit()
                    or not 16000 <= int(length) <= MAX_AUDIO
                    or not secrets.compare_digest(self.headers.get("X-TAFA-CSRF",""),CSRF)):
                return self.send_error(400)
            query=parse_qs(urlsplit(self.path).query)
            kind=query.get("kind",["turn"])
            ident=query.get("conversation_id",[""])
            if len(kind)!=1 or kind[0] != "turn" or len(ident)!=1:
                return self.respond_json({"error":"Invalid voice request"},400)
            payload=self.rfile.read(int(length))
            try:
                result=run_voice(TOKEN,pcm=payload,conversation_id=ident[0])
            except VoiceTestError as exc:
                return self.respond_json({"error":str(exc)},400)
            except (OSError,RuntimeError,TimeoutError,ValueError,TypeError):
                return self.respond_json({"error":"Assist connection unavailable"},503)
            return self.respond_json(result)
        if not length or not length.isdigit() or not 0<int(length)<=16384:
            return self.send_error(400)
        if self.headers.get_content_type()!="application/x-www-form-urlencoded":
            return self.send_error(415)
        fields=parse_qs(self.rfile.read(int(length)).decode("utf-8"),max_num_fields=32,keep_blank_values=True)
        if not secrets.compare_digest(fields.get("csrf",[""])[0],CSRF):
            return self.send_error(403)
        lang="en" if fields.get("lang")==["en"] else "de"
        tab=fields.get("tab",["maintenance"])[0]
        if tab not in ("overview","connections","setup","devices","maintenance","voice"):
            tab="maintenance"
        try:
            action=fields.get("action",["backend"])[0]
            if action=="voice_devices":
                if set(fields) - {"csrf","lang","tab","action"}:
                    return self.respond_json({"error":"Invalid device status request"},400)
                device_state=read_device_data()
                if device_state.get("error"):
                    return self.respond_json({"error":"TAFA device status unavailable"},503)
                return self.respond_json(public_device_snapshot(device_state))
            if action=="voice_device_mode":
                if (set(fields) - {"csrf","lang","tab","action","device_id","mode"}
                        or len(fields.get("device_id",[]))!=1 or len(fields.get("mode",[]))!=1):
                    return self.respond_json({"error":"Invalid native microphone request"},400)
                identifier=fields["device_id"][0]
                target=fields["mode"][0]
                if target not in ("mute","wake","continuous"):
                    return self.respond_json({"error":"Unsupported native microphone mode"},400)
                try:
                    set_native_microphone_mode(identifier,target)
                    current=read_device_data()
                    if current.get("error"):
                        raise RuntimeError("Device status unavailable")
                    return self.respond_json(public_device_snapshot(current))
                except (OSError,TimeoutError,RuntimeError):
                    return self.respond_json({"error":"Tablet update unavailable"},503)
                except (ValueError,TypeError,KeyError):
                    return self.respond_json({"error":"Invalid native microphone request"},400)
            if action=="voice_status":
                if set(fields) - {"csrf","lang","tab","action"}:
                    return self.respond_json({"error":"Invalid voice status request"},400)
                try:
                    return self.respond_json(voice_status(TOKEN))
                except (OSError,TimeoutError,ValueError,RuntimeError,TypeError):
                    return self.respond_json({"error":"Home Assistant status unavailable"},503)
            if action=="voice_text":
                if set(fields) - {"csrf","lang","tab","action","text","conversation_id"}:
                    return self.respond_json({"error":"Invalid voice text request"},400)
                try:
                    return self.respond_json(run_voice(TOKEN,
                        text=fields.get("text",[""])[0],
                        conversation_id=fields.get("conversation_id",[""])[0]))
                except VoiceTestError as exc:
                    return self.respond_json({"error":str(exc)},400)
                except (OSError,TimeoutError,ValueError,RuntimeError,TypeError):
                    return self.respond_json({"error":"Assist connection unavailable"},503)
            if action=="connection_probe":
                # Short, read-only request from a typing event. Strict
                # destination validation in connection_probes prevents SSRF.
                key=fields.get("field",[""])[0]
                value=fields.get("value",[""])[0]
                if (key not in ADDRESS_FIELDS or len(fields.get("field",[]))!=1
                        or len(fields.get("value",[]))!=1 or len(value)>256):
                    return self.respond_json({"status":"invalid","detail":"invalid_input"},400)
                return self.respond_json(probe_connection(key,value))
            if action=="manifest_preview":
                payload=fields.get("manifest_json",[""])[0]
                review=preview_import(payload,load_options())
                self.respond(display(lang=lang,default_tab="connections",review=review))
                return
            elif action=="manifest_apply":
                manifest=consume_import(fields.get("ticket",[""])[0])
                current=load_options()
                changes=reconcile_imported_stt(
                    current,proposed_options(manifest,current),manifest["kind"])
                known=load_records().get(manifest["device_id"],{})
                if known and known.get("kind")!=manifest["kind"]:
                    raise ValueError("Device identity was previously used for a different server type")
                pending=False
                # New installations have the integration files staged but HA
                # Core may not have loaded the custom config flow yet.
                proposed={**current,**changes}
                mode=proposed.get("speech_mode","setup")
                if mode=="external":
                    piper=proposed.get("external_piper_base","")
                else:
                    piper=_internal_address()
                ready=False
                try:
                    # Validate repaired proposed options, not the potentially
                    # conflicting already-saved CPU/GPU mappings.
                    configured=configure(piper,setup_settings_values(proposed))
                    ready=configured in ("configured","already_configured")
                    if not ready:
                        pending=True
                except (urllib.error.URLError,RuntimeError) as exc:
                    if ("flow not available" in str(exc)
                            or isinstance(exc,urllib.error.HTTPError)
                            and exc.code in (404,503)):
                        pending=True
                    else:
                        raise
                if ready:
                    try:
                        results=provision_worker_manifest(manifest,known.get("entries",{}))
                    except RuntimeError as exc:
                        if not ("TAFA HA backend not loaded yet" in str(exc)
                                or "not_configured" in str(exc)):
                            raise
                        results={"entries":{},"entities":{},"messages":["HA Core restart required"]}
                        pending=True
                else:
                    results={"entries":{},"entities":{},"messages":["HA Core restart required"]}
                entries=results.get("entries",{})
                entities=results.get("entities",{})
                if not isinstance(entries,dict) or not isinstance(entities,dict):
                    raise RuntimeError("Invalid HA provisioning result")
                role="gpu_stt" if manifest["kind"]=="gpu_worker" else "cpu_stt"
                if entities.get("stt"):
                    changes[role]=entities["stt"]
                if entities.get("llm_agent") and manifest["kind"]=="gpu_worker":
                    changes["llm_agent"]=entities["llm_agent"]
                changes=reconcile_imported_stt(current,changes,manifest["kind"])
                if changes:
                    save_app_changes(TOKEN,changes,import_kind=manifest["kind"])
                save_record(manifest,entries,pending=pending)
                activate_configured_services()
                notes=results.get("messages",[])
                msg=("JSON importiert; TAFA führt die Einrichtung automatisch fort. / "
                     "JSON imported; TAFA is completing setup automatically. ")
                if pending:
                    if fields.get("restart_core_if_needed",[""])[0]=="1":
                        try:
                            restart_home_assistant_core()
                            msg+=(" Home Assistant Core startet neu; TAFA setzt danach fort. / HA Core restarting; TAFA will resume.")
                        except (OSError,RuntimeError,ValueError) as exc:
                            msg+=(" Core-Neustart fehlgeschlagen: "+str(exc)[:90]+
                                  ". Bitte über Home Assistant einmal Core neu starten.")
                    else:
                        msg+=(" Home Assistant Core muss die neue Integration einmal laden. Ein Neustart ist unter Wartung möglich."
                    )
                if isinstance(notes,list):
                    msg+=" | ".join(str(item)[:160] for item in notes[:4])
                tab="connections"
            elif action=="restart_core":
                if fields.get("confirmation",[""])[0]!="RESTART":
                    raise ValueError("Core restart requires confirmation RESTART")
                restart_home_assistant_core()
                msg="Home Assistant Core startet neu; TAFA setzt vorgemerkte JSON-Importe fort. / HA Core restarting; TAFA will resume pending imports."
            elif action=="models":
                if choose_speech_source()[0] != "local":
                    return self.send_error(400, "Bundled speech disabled in external mode")
                accepted=retry_models()
                msg=("Speech model retry requested / Sprachmodelle erneut gestartet."
                     if accepted else "Speech model retry unavailable / Wiederholung nicht möglich.")
            elif action=="device_update":
                msg=update_device(fields)
                tab="devices"
            elif action=="room_create":
                msg=create_room(fields)
                tab="devices"
            elif action=="room_pair":
                msg=pair_device(fields)
                tab="devices"
            elif action=="room_camera":
                msg=set_room_camera(fields)
                tab="devices"
            elif action=="room_unpair":
                msg=unpair_device(fields)
                tab="devices"
            elif action=="room_delete":
                msg=delete_room(fields)
                tab="devices"
            elif action=="device_delete":
                msg=remove_device(fields)
                tab="devices"
            elif action=="settings":
                changes=save_settings_form(TOKEN,fields,discover_wyoming_stt(TOKEN))
                activate_configured_services()
                msg="Einstellungen gespeichert. TAFA übernimmt die Änderung automatisch. / Settings saved; TAFA is applying changes automatically."
            elif action=="connection_settings":
                # Keep address editing available when HA's entity registry
                # cannot be read. Unchanged provider IDs remain valid; new
                # assignments still require a successful registry lookup.
                try:
                    providers=discover_wyoming_stt(TOKEN)
                except Exception:
                    providers=[]
                save_connection_form(TOKEN,fields,providers)
                activate_configured_services()
                tab="connections"
                msg="Verbindungsadressen gespeichert. / Connection addresses saved."
            elif action=="wyoming":
                choices=discover_wyoming_stt(TOKEN)
                selection=save_wyoming_selection(TOKEN,
                    fields.get("cpu_stt",[""])[0],fields.get("gpu_stt",[""])[0],choices)
                msg=("Wyoming-Auswahl gespeichert. TAFA-App neu starten! / "
                     "Wyoming selection saved. Restart TAFA App! "
                     "CPU="+selection["cpu_stt"]+" GPU="+selection["gpu_stt"])
            elif action=="cleanup":
                if fields.get("confirmation",[""])[0] != "ENTFERNEN":
                    return self.send_error(400, "Explicit deletion confirmation required")
                removed=remove_local_models(choose_speech_source()[0])
                msg=("TAFA downloads removed: "+
                     f"Piper {removed['piper_bytes']} B / Whisper {removed['whisper_bytes']} B")
            elif action=="backend":
                added=bootstrap(CONFIG,BUNDLE)
                msg=("Installed: "+", ".join(added)+". Restart HA." if added
                     else "Existing TAFA files preserved. / Bestehende Dateien bleiben unverändert.")
            else:
                return self.send_error(400)
            self.respond(display(msg,lang=lang,default_tab=tab))
        except (OSError,ValueError,RuntimeError,SyntaxError) as exc:
            reason=(str(exc)[:180] if isinstance(exc,ValueError) or action in ("manifest_preview","manifest_apply") else type(exc).__name__)
            self.respond(display("TAFA configuration: "+reason,lang=lang,default_tab=tab),400)

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    startup()
    ThreadingHTTPServer(("0.0.0.0",8099),Handler).serve_forever()
