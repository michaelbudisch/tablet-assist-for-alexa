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

from auto_setup import configure, ensure_pipeline, save_state, STATE as SETUP_STATE
from installer import bootstrap, status

LOG=logging.getLogger("tafa.app")
CONFIG=Path("/homeassistant")
BUNDLE=Path(__file__).parent/"bundle"
CSRF=secrets.token_urlsafe(32)
REPO="https://github.com/michaelbudisch/tablet-assist-for-alexa"
TOKEN=os.environ.get("SUPERVISOR_TOKEN","")
STATUS_URL="http://127.0.0.1:5000/status"
APP_VERSION="0.3.3"

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

def setup_status():
    try:
        return json.loads(SETUP_STATE.read_text())
    except (OSError,ValueError):
        return {"status":"pending","detail":""}

def autoconfigure(address):
    # Reattempt after HA Core restarts and discovers newly installed files.
    while True:
        try:
            if speech_status().get("piper_ready"):
                outcome=configure(address)
                save_state(outcome)
                if outcome in ("configured","already_configured"):
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
    threading.Thread(target=monitor_speech,daemon=True).start()
    try:
        address=_internal_address()
        publish_service_address(address)
        threading.Thread(target=autoconfigure,args=(address,),daemon=True).start()
        LOG.info("Internal CPU service endpoint registered")
    except (OSError,RuntimeError,ValueError) as exc:
        LOG.error("Automatic HA setup unavailable: %s",type(exc).__name__)
        save_state("needs_attention",type(exc).__name__)

def display(message="",lang="de"):
    en=lang=="en"
    t=lambda de,eng:eng if en else de
    state=status(CONFIG)
    runtime=speech_status()
    setup=setup_status()
    cards=[
      (t("Home-Assistant-Backend","Home Assistant backend"),state.get("tablet_assist_for_alexa","not installed")),
      ("Piper · TTS",t("Bereit","Ready") if runtime.get("piper_ready") else t("Noch nicht bereit","Not ready")),
      ("Whisper · STT",t("Bereit","Ready") if runtime.get("whisper_ready") else t("Noch nicht bereit","Not ready")),
      (t("HA-Einrichtung","HA setup"),setup.get("status","pending"))
    ]
    panels="".join('<div class="tile"><strong>'+html.escape(a)+'</strong><span>'+html.escape(str(b))+'</span></div>' for a,b in cards)
    note=t("Neue Komponenten werden beim App-Start eingebunden. Home Assistant muss danach einmal neu gestartet werden.",
      "New components are staged at app startup. Home Assistant needs one restart afterwards.")
    install=t("Backend erneut prüfen","Check backend installation")
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
<section><h2>{t("Einrichtungsstatus","Setup status")}</h2><p>{html.escape(message or setup.get("detail","") or note)}</p>
<form action="./" method="post"><input type="hidden" name="csrf" value="{CSRF}"><input type="hidden" name="lang" value="{lang}">
<button type="submit">{install}</button></form></section>
<section><h2>{t("Inbetriebnahme","Getting started")}</h2>
<ol class="steps">
<li>{t("TAFA installiert das gemeinsame Backend automatisch, falls es noch fehlt.","TAFA automatically stages the unified backend if missing.")}</li>
<li>{t("Home Assistant einmal über Einstellungen → System neu starten.","Restart Home Assistant once through Settings → System.")}</li>
<li>{t("Die TAFA-Integration und eine eigene Assist-Pipeline werden eingerichtet, sobald Piper verfügbar ist und Home Assistant die Komponenten erkennt.","The TAFA integration and its Assist pipeline are configured when Piper is ready and Home Assistant discovers the components.")}</li>
<li>{t("TAFA Device Bridge auf dem Tablet mit Home Assistant verbinden und die Assist-Pipeline auswählen.","Connect TAFA Device Bridge to Home Assistant and select the Assist pipeline.")}</li>
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
            added=bootstrap(CONFIG,BUNDLE)
            msg=("Installed: "+", ".join(added)+". Restart HA." if added
                 else "Existing TAFA files preserved. / Bestehende Dateien bleiben unverändert.")
            self.respond(display(msg,lang=lang))
        except (OSError,ValueError,SyntaxError) as exc:
            self.respond(display("Installation stopped: "+type(exc).__name__,lang=lang),400)

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    startup()
    ThreadingHTTPServer(("0.0.0.0",8099),Handler).serve_forever()
