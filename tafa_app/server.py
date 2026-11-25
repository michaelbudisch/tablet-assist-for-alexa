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
                           setup_settings, connection_status)
from model_store import inventory as local_model_inventory, remove_local_models

LOG=logging.getLogger("tafa.app")
CONFIG=Path("/homeassistant")
BUNDLE=Path(__file__).parent/"bundle"
CSRF=secrets.token_urlsafe(32)
REPO="https://github.com/michaelbudisch/tablet-assist-for-alexa"
TOKEN=os.environ.get("SUPERVISOR_TOKEN","")
STATUS_URL="http://127.0.0.1:5000/status"
APP_VERSION="0.3.16"

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
    while True:
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
            child = subprocess.Popen([sys.executable,worker])
            code = child.wait()
            LOG.error("CPU speech process exited with code %s; restarting in 10 s",code)
        except OSError as exc:
            LOG.error("CPU speech process could not start: %s",type(exc).__name__)
        time.sleep(10)

def startup():
    try:
        added=bootstrap(CONFIG,BUNDLE)
        if added: LOG.info("Unified TAFA backend staged. Home Assistant must restart to discover it.")
        else: LOG.info("Existing TAFA installation preserved.")
    except (OSError,ValueError,SyntaxError) as exc:
        LOG.error("Backend installation could not complete: %s",type(exc).__name__)
    try:
        mode, external_base = choose_speech_source()
        if mode == "local":
            threading.Thread(target=monitor_speech,daemon=True).start()
            address=_internal_address()
            LOG.info("Bundled CPU Piper and Whisper enabled")
        else:
            address=external_base
            LOG.info("External Proxmox Piper selected; bundled CPU speech disabled")
        publish_service_address(address)
        threading.Thread(target=autoconfigure,args=(address,mode),daemon=True).start()
    except (OSError,RuntimeError,ValueError) as exc:
        LOG.error("Automatic HA setup unavailable: %s",type(exc).__name__)
        save_state("needs_attention",str(exc)[:150])

def display(message="",lang="de"):
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
    links=connection_status(preferences, runtime.get("piper_ready") is True)
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
       t("Kein KI-Agent ausgewählt; Ollama als HA-Integration hinzufügen und unter Apps → TAFA → Konfiguration bei llm_agent auswählen",
         "No AI agent selected; add Ollama as an HA integration, then select it in Apps → TAFA → Configuration → llm_agent")
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
        f'<input type="hidden" name="lang" value="{lang}">'
        f'<label>{t("Zur Bestätigung ENTFERNEN eingeben","Type ENTFERNEN to confirm")}'
        f'<input name="confirmation" type="text" maxlength="10" required pattern="ENTFERNEN" autocomplete="off"></label>'
        f'<button type="submit" name="action" value="cleanup">{t("TAFA-Sprachmodelle löschen","Delete TAFA speech models")}</button>'
        f'</form>' if mode == "external" and has_cache else "")
    guide = f"""
<section><h2>{t("Einrichtung in vier Schritten", "Setup in four steps")}</h2>
<p class="muted">{t("Wähle nur die Funktionen, die du tatsächlich brauchst. TAFA ändert keine Proxmox-Container, GPU-Worker oder Router-Einstellungen automatisch.", "Configure only what you need. TAFA does not modify Proxmox containers, GPU workers or router settings automatically.")}</p>
<div class="tiles">
<div class="tile"><strong>1 · {t("Sprachserver", "Speech server")}</strong>
<p><b>{t("A: Alles in TAFA (Standard)", "A: Everything in TAFA (default)")}</b></p>
<p>{t("Piper und Whisper laufen lokal in dieser App, wenn als App-Option speech_mode=local gewählt ist. Keine weitere VM nötig.", "Piper and Whisper run locally with App option speech_mode=local. No additional VM required.")}</p>
<p><b>{t("B: Proxmox-Sprachserver", "B: Proxmox speech server")}</b></p>
<p>{t("Bei Apps → TAFA → Konfiguration speech_mode=external und external_piper_base=http://SERVER:5000 setzen, danach App neu starten. Dann in HA Wyoming-STT von SERVER:10300 ergänzen Die Wyoming-Entitäts-ID bei Apps → TAFA → Konfiguration eintragen (oder bei genau einer STT-Entität automatisch erkennen lassen). Es werden keine lokalen Sprachmodelle geladen.", "In Apps → TAFA → Configuration choose speech_mode=external and external_piper_base=http://SERVER:5000, then restart the App. Add Wyoming STT from SERVER:10300 in HA and set its entity ID in Apps → TAFA → Configuration (or auto-select when exactly one Wyoming STT exists). No local CPU models are loaded.")}</p>
<a href="{REPO}/blob/main/docs/{'en/' if en else ''}proxmox.md" target="_blank" rel="noopener">{t("Proxmox-Anleitung", "Proxmox guide")}</a>
</div>
<div class="tile"><strong>2 · {t("GPU-Hauptrechner (optional)", "GPU computer (optional)")}</strong>
<p>{t("Qwen-Streaming auf Port 10502. Die Windows-BAT-Dateien erzeugen bei Bedarf eine .env ohne API-Token. Die GPU-Adresse unter Optionen → Sprachserver & GPU eintragen.", "Qwen streaming uses port 10502. The Windows BAT files create an optional .env without API tokens. Configure the GPU URL under Options → Speech servers & GPU.")}</p>
<p>{t("Automatisch: Qwen, wenn bereit; sonst Piper. Keine automatische Netzwerksuche.", "Automatic: Qwen if ready; otherwise Piper. No network scanning.")}</p>
<a href="{REPO}/blob/main/docs/{'en/' if en else ''}worker.md" target="_blank" rel="noopener">{t("GPU-Worker einrichten", "Set up GPU worker")}</a>
</div>
<div class="tile"><strong>3 · {t("Text-KI für freie Fragen (Ollama)", "Text AI for open questions (Ollama)")}</strong>
<p>{t("Qwen-TTS auf Port 10502 spricht nur die Antwort. Für Wissensfragen Ollama auf dem GPU-PC (meist Port 11434) als Home-Assistant-Integration hinzufügen. Dort ein Textmodell wie qwen3:4b-instruct wählen und in Apps → TAFA → Konfiguration bei llm_agent dessen conversation-Entität eintragen. Danach TAFA-App neu starten. Keine automatischen Modelldownloads.",
"Qwen TTS on port 10502 only speaks the reply. For general questions, add Ollama from the GPU PC (usually port 11434) as a Home Assistant integration, select a text model such as qwen3:4b-instruct, and set llm_agent to its conversation entity in Apps → TAFA → Configuration. Restart TAFA App afterwards. No automatic model downloads.")}</p>
<a href="{REPO}/blob/main/docs/{'en/' if en else ''}worker.md" target="_blank" rel="noopener">{t("Text-KI-Anleitung", "Text AI guide")}</a>
</div>
<div class="tile"><strong>4 · {t("Alexa-Durchsagen (optional)", "Alexa announcements (optional)")}</strong>
<p>{t("Nur für Alexa-MP3-Durchsagen: Generator 5001, temporäre Dateien 8080 und gesonderter öffentlicher HTTPS-Proxy. Bei Bluetooth-Ausgabe an den Echo nicht nötig.", "Only for Alexa MP3 announcements: generator 5001, temporary files 8080, and a separate public HTTPS proxy. Not needed for Echo Bluetooth output.")}</p>
<p>{t("Einstellungen unter Optionen → Alexa-Durchsagen & HTTPS.", "Configure under Options → Alexa announcements & HTTPS.")}</p>
<a href="{REPO}/blob/main/docs/{'en/' if en else ''}nginx-proxy.md" target="_blank" rel="noopener">{t("HTTPS-Anleitung", "HTTPS guide")}</a>
</div>
</div>
<p><a href="/config/integrations/integration/tablet_assist_for_alexa" target="_top">{t("TAFA-Integration öffnen → Optionen", "Open TAFA integration → Options")}</a></p>
</section>
"""
    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Cache-Control" content="no-store">
<title>TAFA · Control Center</title>
<style>
:root{{font:15px/1.5 system-ui,-apple-system,sans-serif;color-scheme:light dark;--accent:#259f8f}}
*{{box-sizing:border-box}}body{{max-width:1000px;margin:0 auto;padding:22px 16px}}
h1{{font-size:27px;margin:0}}h2{{font-size:17px;margin:0 0 8px}}p{{margin:8px 0}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}}
small,.muted{{opacity:.7}}.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:20px 0}}
.tile,section{{border:1px solid #80808055;background:color-mix(in srgb,canvas 96%,var(--accent));border-radius:13px;padding:16px}}
.tile strong,.tile span{{display:block}}.tile span{{font-size:13px;margin-top:8px;overflow-wrap:anywhere}}
section{{margin:13px 0}}a,button{{font:inherit}}a{{color:var(--accent)}}button{{border:1px solid var(--accent);background:var(--accent);color:#fff;padding:10px 15px;border-radius:9px;cursor:pointer}}
nav a{{margin-right:12px}}.steps{{padding-left:23px}}li{{margin:7px 0}}
</style></head>
<body>
<div class="top"><div><h1>TAFA Control Center</h1><small>{t("Lokaler Sprachassistent","Local voice assistant")} · {APP_VERSION} · Beta</small></div>
<nav><a href="?lang=de">Deutsch</a><a href="?lang=en">English</a></nav></div>
<div class="tiles">{panels}</div>
<section id="connections"><h2>{t("Verbindungsdiagnose", "Connection diagnostics")}</h2>
<p>{t("Abfragen der eingerichteten GPU-/Piper-/MP3-Health-Endpunkte. Kein Test-Audio und keine Durchsage werden erzeugt.", "Checks the configured GPU, Piper and MP3 health endpoints. No speech or announcements are generated.")}</p>
<p><a href="?lang={lang}#connections">{t("Verbindungen jetzt erneut prüfen", "Check connections now")}</a></p>
<p class="muted">{t("Die Sprachausgabe-Prognose stammt aus den App-Optionen. Bei bestehenden HA-Integrationen müssen abweichende Optionen dort separat angeglichen werden.", "The predicted speech route uses App options. Existing HA integration settings may need to be aligned separately.")}</p>
</section>
{guide}
<section><h2>{t("Einrichtungsstatus","Setup status")}</h2><p>{html.escape(message or setup.get("detail","") or note)}</p>
<form action="./" method="post"><input type="hidden" name="csrf" value="{CSRF}"><input type="hidden" name="lang" value="{lang}">
<button type="submit" name="action" value="backend">{install}</button>
{retry_button}</form></section>
<section><h2>{t("Lokale Sprachmodelle verwalten","Manage local speech models")}</h2>
<p>{cache_info}</p>
<p class="muted">{t("Es werden ausschließlich TAFA-eigene Piper-/Whisper-Downloads aus /data/tafa_speech verwaltet, keine Modelle aus Proxmox, Wyoming oder anderen Home-Assistant-Apps.", "Only TAFA-owned Piper/Whisper downloads in /data/tafa_speech are managed; Proxmox, Wyoming and other Home Assistant apps are untouched.")}</p>
<p class="muted">{t("Zum Löschen zuerst in der App-Konfiguration external wählen und TAFA neu starten. Dadurch wird der lokale Sprachprozess beendet; ein unbeabsichtigtes erneutes Herunterladen wird verhindert.", "To delete, first select external in App Configuration and restart TAFA. This stops local speech so models cannot be redownloaded automatically.")}</p>
{remove_button}
</section>
<section><h2>{t("Inbetriebnahme","Getting started")}</h2>
<ol class="steps">
<li>{t("TAFA installiert das gemeinsame Backend automatisch, falls es noch fehlt.","TAFA automatically stages the unified backend if missing.")}</li>
<li>{t("Home Assistant einmal über Einstellungen → System neu starten.","Restart Home Assistant once through Settings → System.")}</li>
<li>{t("Im lokalen Modus wird die TAFA-Lokal-Pipeline automatisch eingerichtet. Im externen Modus Wyoming-STT einrichten; bei genau einer STT-Entität erfolgt die Auswahl automatisch, andernfalls cpu_stt in der TAFA-App wählen. Danach erstellt TAFA die Assist-Pipeline.","Local mode can auto-create the TAFA Lokal pipeline. In external mode configure Wyoming STT and its entity in the TAFA App; TAFA then automatically creates the complete Assist pipeline.")}</li>
<li>{t("TAFA Device Bridge für Rufwort/Audio verbinden. Die Pipeline in Home Assistant Assist auswählen; die Bridge selbst überträgt keine anschließende Frage.","Connect Device Bridge for wake events/audio. Select the Assist pipeline in Home Assistant; the Bridge does not transmit the following spoken question.")}</li>
</ol><p><a href="/config/integrations" target="_top">{t("Geräte & Dienste öffnen","Open devices & services")}</a>
 · <a href="/tablet_assist_for_alexa" target="_top">{t("TAFA Sprachzentrale","TAFA voice center")}</a></p>
<p class="muted">{t("Externe GPU ist optional. Kameras und Mikrofone werden nicht automatisch aktiviert.","External GPU is optional. Cameras and microphones are never activated automatically.")}</p></section>
<section><h2>{t("Anleitungen & Support","Guides & support")}</h2>
<a href="{REPO}/blob/main/docs/app.md" target="_blank" rel="noopener">DE</a>
 · <a href="{REPO}/blob/main/docs/en/app.md" target="_blank" rel="noopener">EN</a>
 · <a href="{REPO}/tree/main/android" target="_blank" rel="noopener">Device Bridge</a>
 · <a href="{REPO}/issues" target="_blank" rel="noopener">GitHub Issues</a>
<p class="muted">{t("Dein privates Dashboard wird nicht installiert oder verändert.","Your private dashboard is never installed or modified.")}</p></section>
</body></html>"""

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
        self.send_header("Content-Security-Policy","default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'self'; base-uri 'none'")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    def do_GET(self):
        if not self.allowed():return self.send_error(403)
        query=parse_qs(urlsplit(self.path).query)
        lang="en" if query.get("lang")==["en"] else "de"
        self.respond(display(lang=lang))
    def do_POST(self):
        if not self.allowed():return self.send_error(403)
        length=self.headers.get("Content-Length")
        if not length or not length.isdigit() or not 0<int(length)<=2048:
            return self.send_error(400)
        if self.headers.get_content_type()!="application/x-www-form-urlencoded":
            return self.send_error(415)
        fields=parse_qs(self.rfile.read(int(length)).decode("utf-8"),max_num_fields=5)
        if not secrets.compare_digest(fields.get("csrf",[""])[0],CSRF):
            return self.send_error(403)
        lang="en" if fields.get("lang")==["en"] else "de"
        try:
            action=fields.get("action",["backend"])[0]
            if action=="models":
                if choose_speech_source()[0] != "local":
                    return self.send_error(400, "Bundled speech disabled in external mode")
                accepted=retry_models()
                msg=("Speech model retry requested / Sprachmodelle erneut gestartet."
                     if accepted else "Speech model retry unavailable / Wiederholung nicht möglich.")
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
            self.respond(display(msg,lang=lang))
        except (OSError,ValueError,SyntaxError) as exc:
            self.respond(display("Installation stopped: "+type(exc).__name__,lang=lang),400)

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    startup()
    ThreadingHTTPServer(("0.0.0.0",8099),Handler).serve_forever()
