"""Validated TAFA worker/CT manifest import and non-destructive change planning.

Never accepts Internet hosts for LAN services, unchecked ports, credentials,
arbitrary Home Assistant entity IDs, model download instructions or shell text.
Only administrator-confirmed previews can be applied by server.py.
"""
import html
import ipaddress
import json
from pathlib import Path
import re
import secrets
import threading
import time
import uuid

SCHEMA="tafa-connection-v1"
RECORD=Path("/data/tafa-imported-devices.json")
LOCK=threading.Lock()
PENDING={}
PRIVATE_NETS=tuple(ipaddress.ip_network(net) for net in
                   ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"))
KINDS={
    "gpu_worker": {"wyoming_stt","qwen_tts","ollama"},
    "speech_server": {"wyoming_stt","piper","mp3","https_audio"},
}
PORTS={"wyoming_stt":10300,"qwen_tts":10502,"ollama":11434,
       "piper":5000,"mp3":5001}
URL_FIELDS={"qwen_tts","ollama","piper","mp3"}


def private_ip(value):
    if not isinstance(value,str):
        raise ValueError("Host must be a private IPv4 address")
    try:
        address=ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError("Host must be a private IPv4 address") from exc
    if address.version != 4 or not any(address in net for net in PRIVATE_NETS):
        raise ValueError("Only private RFC1918 IPv4 is allowed")
    return str(address)


def validate(source):
    if not isinstance(source,str) or not 0 < len(source.encode("utf-8")) <= 10000:
        raise ValueError("JSON must be 1-10000 bytes")
    def unique_keys(pairs):
        out={}
        for key,val in pairs:
            if key in out:
                raise ValueError("Duplicate JSON keys are not allowed")
            out[key]=val
        return out
    try:
        data=json.loads(source,object_pairs_hook=unique_keys)
    except (TypeError,json.JSONDecodeError) as exc:
        raise ValueError("Invalid JSON") from exc
    if not isinstance(data,dict) or set(data)!={"schema","kind","device_id","host","services"}:
        raise ValueError("Unexpected manifest fields")
    if data["schema"]!=SCHEMA or data["kind"] not in KINDS:
        raise ValueError("Unsupported TAFA manifest format or device type")
    try:
        device_id=str(uuid.UUID(str(data["device_id"])))
    except (ValueError,TypeError,AttributeError) as exc:
        raise ValueError("Invalid stable device ID") from exc
    host=private_ip(data["host"])
    services=data["services"]
    if not isinstance(services,dict) or set(services)!=KINDS[data["kind"]]:
        raise ValueError("Missing/unknown services for device type")
    normalized={}
    for name,entry in services.items():
        if not isinstance(entry,dict) or type(entry.get("enabled")) is not bool:
            raise ValueError("Service enabled flag must be boolean")
        allowed={"enabled","host","port"} if name=="wyoming_stt" else \
                {"enabled","url","model"} if name=="ollama" else {"enabled","url"}
        if set(entry)!=allowed:
            raise ValueError("Invalid fields for "+name)
        enabled=entry["enabled"]
        if name=="wyoming_stt":
            if entry["host"]!=host or type(entry["port"]) is not int or entry["port"]!=10300:
                raise ValueError("Wyoming host/port mismatch")
            normalized[name]={"enabled":enabled,"host":host,"port":10300}
        elif name=="https_audio":
            url=entry["url"]
            if not isinstance(url,str) or len(url)>254:
                raise ValueError("Invalid HTTPS URL")
            if url:
                from urllib.parse import urlsplit
                parsed=urlsplit(url)
                if (parsed.scheme!="https" or not parsed.hostname
                        or not re.fullmatch(r"[A-Za-z0-9.-]{4,253}",parsed.hostname)
                        or parsed.username or parsed.password or parsed.path
                        or parsed.query or parsed.fragment
                        or (parsed.port not in (None,443))):
                    raise ValueError("Invalid public audio URL")
            if enabled and not url:
                raise ValueError("Enabled public audio requires a URL")
            normalized[name]={"enabled":enabled,"url":url}
        else:
            url=entry["url"]
            expected=f"http://{host}:{PORTS[name]}"
            if url!=expected:
                raise ValueError("Service URL must match its private host and port: "+name)
            normalized[name]={"enabled":enabled,"url":expected}
            if name=="ollama":
                model=entry["model"]
                if not isinstance(model,str) or len(model)>100 or (
                    model and not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}",model)):
                    raise ValueError("Invalid Ollama model name")
                normalized[name]["model"]=model
    return {"schema":SCHEMA,"kind":data["kind"],
            "device_id":device_id,"host":host,"services":normalized}


def proposed_options(manifest, current):
    services=manifest["services"]
    delta={}
    if manifest["kind"]=="gpu_worker":
        if services["qwen_tts"]["enabled"]:
            delta["gpu_base"]=services["qwen_tts"]["url"]
            delta["hardware_profile"]="automatic"
        if services["wyoming_stt"]["enabled"]:
            delta["gpu_stt_host"]=manifest["host"]
    else:
        if services["piper"]["enabled"]:
            delta["speech_mode"]="external"
            delta["external_piper_base"]=services["piper"]["url"]
        if services["mp3"]["enabled"]:
            delta["mp3_base"]=services["mp3"]["url"]
        if services["https_audio"]["enabled"]:
            delta["public_audio_base"]=services["https_audio"]["url"]
    return {key:value for key,value in delta.items() if current.get(key)!=value}


def load_records(path=RECORD):
    try:
        rows=json.loads(path.read_text(encoding="utf-8"))
        return rows if isinstance(rows,dict) else {}
    except (OSError,ValueError):
        return {}


def save_record(manifest, entry_ids, path=RECORD):
    """Only track an imported device's identity, host, and assigned HA entries."""
    with LOCK:
        rows=load_records(path)
        previous=rows.get(manifest["device_id"],{})
        kept={k:v for k,v in previous.get("entries",{}).items()
              if k in ("wyoming_stt","ollama") and isinstance(v,str)}
        kept.update({k:v for k,v in entry_ids.items()
                     if k in ("wyoming_stt","ollama") and isinstance(v,str)})
        rows[manifest["device_id"]]={
            "kind":manifest["kind"],"host":manifest["host"],"entries":kept}
        path.parent.mkdir(parents=True,exist_ok=True)
        draft=path.with_suffix(".json.tmp")
        draft.write_text(json.dumps(rows,sort_keys=True),encoding="utf-8")
        draft.chmod(0o600)
        draft.replace(path)


def preview(manifest_text, options):
    manifest=validate(manifest_text)
    with LOCK:
        # Short-lived in-memory confirmation; no unconfirmed file is persisted.
        now=time.monotonic()
        for key in list(PENDING):
            if now-PENDING[key]["created"]>600:
                del PENDING[key]
        ticket=secrets.token_urlsafe(24)
        PENDING[ticket]={"manifest":manifest,"created":now}
    changes=proposed_options(manifest,options)
    previous=load_records().get(manifest["device_id"])
    return ticket,manifest,changes,previous


def consume(ticket):
    if not isinstance(ticket,str) or len(ticket)>70:
        raise ValueError("Invalid confirmation")
    with LOCK:
        pending=PENDING.pop(ticket,None)
    if not pending or time.monotonic()-pending["created"]>600:
        raise ValueError("Import confirmation expired; preview the JSON again")
    return pending["manifest"]


def render_panel(lang,csrf,notice="",review=None):
    en=lang=="en"
    t=lambda de,eng:eng if en else de
    esc=lambda s:html.escape(str(s or ""),quote=True)
    confirmation=""
    if review:
        ticket,manifest,changes,previous=review
        changes_html="".join(
            f'<li><code>{esc(k)}</code>: {esc(v)}</li>'
            for k,v in changes.items()) or f'<li>{t("Keine TAFA-Adressen müssen geändert werden.","No TAFA addresses need to change.")}</li>'
        status=t("Bekanntes Gerät – IP-Update","Known device – IP update") if previous and previous.get("host")!=manifest["host"] else t("Bekanntes Gerät","Known device") if previous else t("Neues Gerät","New device")
        service_list="".join(
            f'<li>{esc(k)}: {t("aktiv","enabled") if v["enabled"] else t("nicht aktiv","not running")}</li>'
            for k,v in manifest["services"].items())
        prior=previous.get("entries",{}) if previous else {}
        intents=[]
        if manifest["services"]["wyoming_stt"]["enabled"]:
            intents.append(t("Wyoming-STT automatisch anlegen oder wiederverwenden; bei bekannter Geräte-ID den Host aktualisieren.",
                             "Set up/reuse Wyoming STT and update mapped entry host when its IP changes."))
        if manifest["kind"]=="gpu_worker" and manifest["services"]["ollama"]["enabled"]:
            intents.append(t("Ollama-Anbindung und vorhandenen Gesprächsagenten prüfen oder ergänzen (kein automatischer Modelldownload).",
                             "Set up/reuse Ollama and its conversation agent (no automatic model download)."))
        action_items="".join("<li>"+esc(item)+"</li>" for item in intents)
        mapping_note=(", "+t("Zugeordnete HA-Integrationen: ","Mapped HA integrations: ")+
                      ", ".join(esc(key) for key in prior)) if prior else ""
        confirmation=f"""<div class="import-review" role="region">
<h4>{t("Änderungen vor der Übernahme prüfen","Review before applying")}</h4>
<p><strong>{esc(status)}</strong> · {esc(manifest["kind"])} · {esc(manifest["host"])}{mapping_note}</p>
<p>{t("Erkannte Dienste","Detected services")}:</p><ul>{service_list}</ul>
<p>{t("Geplante Home-Assistant-Aktionen","Planned Home Assistant actions")}:</p><ul>{action_items}</ul>
<p>{t("TAFA-Optionen werden angepasst","TAFA options to update")}:</p><ul>{changes_html}</ul>
<p class="subtle">{t("Wyoming und Ollama werden erst nach deiner Bestätigung eingerichtet. Bestehende, nicht zugeordnete Integrationen bleiben unverändert.","Wyoming and Ollama are provisioned only after confirmation. Unrelated existing integrations remain unchanged.")}</p>
<form action="./" method="post">
<input type="hidden" name="csrf" value="{esc(csrf)}">
<input type="hidden" name="lang" value="{esc(lang)}">
<input type="hidden" name="tab" value="setup">
<input type="hidden" name="ticket" value="{esc(ticket)}">
<button class="btn btn-primary" type="submit" name="action" value="manifest_apply">{t("Änderungen übernehmen","Apply reviewed changes")}</button>
</form></div>"""
    return f"""<section class="import-card" id="manifest-import">
<div class="import-header"><div><p class="kicker">JSON IMPORT</p>
<h3>{t("Worker automatisch einrichten","Set up a worker automatically")}</h3>
<p>{t("Worker- oder Proxmox-JSON auswählen. TAFA zeigt alle Änderungen vor der Übernahme an.","Choose a worker or Proxmox JSON. TAFA previews every change before applying.")}</p></div></div>
<form action="./" method="post">
<input type="hidden" name="csrf" value="{esc(csrf)}">
<input type="hidden" name="lang" value="{esc(lang)}">
<input type="hidden" name="tab" value="setup">
<label for="manifest-file">{t("JSON-Datei auswählen","Select JSON file")}</label>
<input type="file" id="manifest-file" accept=".json,application/json">
<label for="manifest-json">{t("JSON-Konfiguration","JSON configuration")}</label>
<textarea id="manifest-json" name="manifest_json" maxlength="10000" rows="6"
placeholder='{{"schema":"tafa-connection-v1",...}}' required></textarea>
<p class="subtle">{t("Datei auswählen oder JSON hier einfügen. Die Datei wird nur lokal im Browser gelesen.","Choose a file or paste JSON here. File reading stays in your browser.")}</p>
<button class="btn btn-outline" type="submit" name="action" value="manifest_preview">{t("Konfiguration prüfen","Preview configuration")}</button>
</form>
{confirmation}
</section>"""
