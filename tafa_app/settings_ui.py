"""One admin-only settings editor for the Supervisor-managed TAFA App options.

The native HA App Configuration and this UI share /data/options.json. Changes are
validated before storing and require a TAFA App restart to apply. No second store.
"""
import html
import json
import urllib.request

from speech_source import load_options, private_http_origin, setup_settings_values
from endpoint_checks import suggested_gpu_stt_host
from wyoming_picker import SUPERVISOR_OPTIONS

CHOICES = {
    "speech_mode": ("local", "external"),
    "hardware_profile": ("automatic", "cpu"),
    "voice_variant": ("default", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
    "live_profile": ("natural", "studio", "clear"),
    "conversation_mode": ("intelligent", "automatic", "manual"),
    "mp3_profile": ("natural", "studio", "announcement"),
}
TEXT_FIELDS = (
    "external_piper_base", "gpu_base", "gpu_stt_host", "llm_agent",
    "mp3_base", "public_audio_base", "rooms_json", "sources_json",
    "reminder_room", "cpu_stt", "gpu_stt",
)
BOOL_FIELDS = ("chime", "learning_enabled", "reminders_enabled")
FORM_FIELDS = frozenset((*CHOICES, *TEXT_FIELDS, *BOOL_FIELDS))


def _value(options, key):
    value = options.get(key, "")
    return str(value or "") if key not in ("rooms_json", "sources_json") else str(value or "{}")


def render_settings_form(options, wyoming, lang, csrf, note, checks=None, latest=None):
    """Display one clear DE/EN settings page; all existing HA App options remain editable."""
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    esc = lambda val: html.escape(str(val), quote=True)
    checks = checks or {}
    status_text = {
        'reachable': t('Erreichbar', 'Reachable'),
        'ready': t('Bereit', 'Ready'),
        'busy': t('Beschäftigt', 'Busy'),
        'offline': t('Nicht erreichbar', 'Unreachable'),
        'not_ready': t('Erreichbar, nicht bereit', 'Reachable, not ready'),
        'not_configured': t('Nicht eingerichtet', 'Not configured'),
        'missing': t('Nicht eingerichtet', 'Not configured'),
        'invalid': t('Ungültige private LAN-Adresse', 'Invalid private LAN address'),
        'configured_unchecked': t('Eingetragen – nicht live geprüft', 'Configured – not checked live'),
        'selected': t('In Home Assistant gefunden', 'Found in Home Assistant'),
        'unverified': t('Entität momentan nicht gefunden', 'Entity currently not found'),
        'unused': t('Bei lokalem Piper nicht verwendet', 'Unused with local Piper'),
    }
    def status_line(name):
        state = checks.get(name)
        if not state:
            return ''
        label = status_text.get(state, str(state))
        detail = ''
        if name == 'gpu_stt_host' and state == 'reachable':
            detail = t(' (TCP 10300, kein Spracherkennungstest)', ' (TCP 10300, not a recognition test)')
        if name in ('gpu_stt', 'cpu_stt') and state == 'selected':
            detail = t(' (keine Live-Audio-Prüfung)', ' (not a live audio test)')
        return f'<p class="muted endpoint-check">{t("Status", "Status")}: {esc(label+detail)}</p>'

    def field(name, label, hint="", placeholder=""):
        maximum = 4096 if name.endswith("_json") else 256
        current = esc(_value(options, name))
        if name == 'gpu_stt_host' and not _value(options, name):
            suggested = suggested_gpu_stt_host(options.get('gpu_base', ''))
            if suggested:
                current = esc(suggested)
                hint = (hint + ' ' + t('Aus der Qwen-IP vorgeschlagen; nur korrekt, wenn Whisper auf demselben Rechner läuft.',
                                     'Suggested from Qwen IP; use only if Whisper runs on the same computer.')).strip()
        if name.endswith("_json"):
            control = f'<textarea id="{name}" name="{name}" maxlength="{maximum}">{current}</textarea>'
        else:
            control = (f'<input id="{name}" name="{name}" type="text" '
                       f'value="{current}" maxlength="{maximum}" placeholder="{esc(placeholder)}">')
        return f'<label for="{name}">{label}</label>{control}' + (f'<p class="muted">{hint}</p>' if hint else "") + status_line(name)

    def select(name, label, entries, selected=None):
        selected = _value(options, name) if selected is None else selected
        choices = []
        for value, title in entries:
            choices.append(f'<option value="{esc(value)}"{" selected" if selected == value else ""}>{esc(title)}</option>')
        return f'<label for="{name}">{label}</label><select name="{name}" id="{name}">{"".join(choices)}</select>' + status_line(name)

    def check(name, label):
        return (f'<label><input type="checkbox" name="{name}" value="1"'
                f'{" checked" if options.get(name) is True else ""}> {label}</label>')

    def stt_picker(name, label):
        selected = _value(options, name)
        entries = [("", t("Keine", "None"))]
        for item in wyoming:
            name_label = item.get("name") or item["id"]
            label_text = name_label + (" · " + item["id"] if name_label != item["id"] else "")
            entries.append((item["id"], label_text))
        if selected and selected not in {x[0] for x in entries}:
            entries.append((selected, selected + " · " + t("momentan nicht gefunden", "currently unavailable")))
        return select(name, label, entries, selected)

    recent = ""
    if latest and latest.get("backend") in ("zusatzrechner", "homeserver"):
        label = t("GPU-Whisper", "GPU Whisper") if latest["backend"] == "zusatzrechner" else t("CPU-/Homeserver", "CPU/homeserver")
        duration = latest.get("duration_ms")
        duration_label = (" · " + str(round(duration)) + " ms") if isinstance(duration, (int, float)) else ""
        recent = '<p class="muted">' + t("Letzte Spracherkennung: ", "Last speech recognition: ") + esc(label + duration_label) + '</p>'

    return f"""
<section id="tafa-settings">
<h2>{t("Einstellungen – zentral verwalten", "Settings – one place")}</h2>
<p>{t("Hier richtest du TAFA vollständig ein. Alle Werte landen direkt in derselben Home-Assistant-App-Konfiguration. Die technische Konfigurationsseite wird nur für Fehlerbehebung benötigt.",
"Configure TAFA here. All values are saved directly to the same Home Assistant App configuration. The technical configuration page is only needed for troubleshooting.")}</p>
<form action="./" method="post">
<input type="hidden" name="csrf" value="{esc(csrf)}">
<input type="hidden" name="lang" value="{esc(lang)}">
<details open><summary>1 · {t("Sprachserver und Whisper", "Speech server and Whisper")}</summary>
{select("speech_mode",t("Wo läuft Piper?", "Where does Piper run?"),
 [("local",t("In der TAFA-App (einfach)", "Inside TAFA (simple)")),
  ("external",t("Extern auf Proxmox", "External Proxmox server"))])}
{field("external_piper_base",t("Proxmox-Piper (Adresse samt Port 5000)", "Proxmox Piper (URL with port 5000)"),
 t("Im lokalen Modus ignoriert.", "Ignored in local mode."),"http://192.168.1.50:5000")}
<div id="wyoming-picker"><p class="muted">{esc(note)}</p>{recent}
{stt_picker("cpu_stt",t("CPU-Whisper / Proxmox", "CPU Whisper / Proxmox"))}
{stt_picker("gpu_stt",t("GPU-Whisper / Windows (optional)", "GPU Whisper / Windows (optional)"))}
<p class="muted">{t("Wyoming einmal in Home Assistant unter Geräte & Dienste hinzufügen. Anschließend hier auswählen.", "Add Wyoming once under Home Assistant Devices & services, then select it here.")}</p>
<p><a href="/config/integrations" target="_top">{t("Wyoming in Home Assistant hinzufügen", "Add Wyoming in Home Assistant")}</a></p></div>
</details>
<details open><summary>2 · {t("GPU, KI und Gesprächssteuerung", "GPU, AI and conversation")}</summary>
{field("gpu_base",t("Qwen-Sprachausgabe (Adresse samt Port 10502)", "Qwen speech (URL with port 10502)"),"","http://192.168.1.60:10502")}
{field("gpu_stt_host",t("GPU-Whisper-IP (nur IP, ohne Port)", "GPU Whisper IP (IP only, no port)"))}
{field("llm_agent",t("Text-KI: Home-Assistant-Gesprächsentität", "Text AI: Home Assistant conversation entity"),
 t("Ollama zuerst unter Geräte & Dienste hinzufügen. Beispiel: conversation.ollama.", "Add Ollama in Devices & services first. Example: conversation.ollama."),"conversation.ollama")}
{select("hardware_profile",t("Sprachausgabe", "Speech output"),
 [("automatic",t("Automatisch: GPU, sonst Piper", "Automatic: GPU then Piper")),
  ("cpu",t("Immer Piper verwenden", "Always use Piper"))])}
{select("conversation_mode",t("Gesprächsverhalten", "Conversation behavior"),
 [("intelligent",t("Intelligent (empfohlen)", "Intelligent (recommended)")),
  ("automatic",t("Automatisch", "Automatic")),("manual",t("Manuell", "Manual"))])}
</details>
<details><summary>3 · {t("Stimme und Klang", "Voice and sound")}</summary>
{select("voice_variant",t("Qwen-Stimmvariante", "Qwen voice variant"),
 [(i,t("Standard", "Default") if i == "default" else i) for i in CHOICES["voice_variant"]])}
{select("live_profile",t("Klangprofil", "Sound profile"),
 [(i,i.title()) for i in CHOICES["live_profile"]])}
</details>
<details><summary>4 · {t("Alexa-Durchsagen (optional)", "Alexa announcements (optional)")}</summary>
{field("mp3_base",t("MP3-Generator (Adresse samt Port 5001)", "MP3 generator (URL with port 5001)"),"","http://192.168.1.50:5001")}
{field("public_audio_base",t("Öffentliche Audio-HTTPS-Adresse (keine LAN-IP)", "Public audio HTTPS URL (not a LAN IP)"),"","https://audio.example.org")}
{select("mp3_profile",t("Durchsage-Klang", "Announcement sound"),[(i,i.title()) for i in CHOICES["mp3_profile"]])}
{check("chime",t("Hinweiston verwenden", "Use chime"))}
{field("rooms_json",t("Alexa-Raumzuordnung (JSON, erweitert)", "Alexa room mapping (JSON, advanced)"))}
</details>
<details><summary>5 · {t("Daten und Erweiterungen", "Data and advanced options")}</summary>
{field("sources_json",t("Home-Assistant-Datenquellen (JSON)", "Home Assistant data sources (JSON)"))}
{check("learning_enabled",t("Lernfunktionen aktivieren", "Enable learning features"))}
{check("reminders_enabled",t("Erinnerungen aktivieren", "Enable reminders"))}
{field("reminder_room",t("Erinnerungsraum (wenn eingerichtet)", "Reminder room (if configured)"))}
</details>
<p class="muted">{t("Die Felder werden vor dem Speichern geprüft. Andere TAFA-Einstellungen bleiben erhalten. Nach dem Speichern die TAFA-App einmal neu starten.",
"Fields are validated before saving; unrelated options remain intact. Restart the TAFA App once after saving.")}</p>
<button type="submit" name="action" value="settings">{t("Einstellungen speichern", "Save settings")}</button>
</form></section>
"""


def validate_settings_form(fields, current, available):
    """Require the complete editor submission; preserve unrelated App keys."""
    required = FORM_FIELDS - set(BOOL_FIELDS)
    if not required.issubset(fields):
        raise ValueError("Incomplete TAFA settings form")
    if set(fields) - FORM_FIELDS - {"csrf", "lang", "action"}:
        raise ValueError("Unknown TAFA settings field")
    if any(len(parts) != 1 for parts in fields.values()):
        raise ValueError("Duplicate TAFA settings field")
    update = {}
    for key in required:
        value = fields[key][0]
        if not isinstance(value, str) or len(value) > (4096 if key.endswith("_json") else 256):
            raise ValueError("Invalid TAFA settings field: " + key)
        update[key] = value
    for key in BOOL_FIELDS:
        value = fields.get(key, [""])[0]
        if value not in ("", "1"):
            raise ValueError("Invalid checkbox: " + key)
        update[key] = value == "1"
    for name, choices in CHOICES.items():
        if update[name] not in choices:
            raise ValueError("Invalid selection: " + name)
    if update["speech_mode"] == "external":
        private_http_origin(update["external_piper_base"])
    candidate = {**current, **update}
    setup_settings_values(candidate)
    valid = {item["id"] for item in available}
    for key in ("cpu_stt", "gpu_stt"):
        if update[key] and update[key] not in valid and update[key] != current.get(key, ""):
            raise ValueError("Wyoming entity is not registered: " + key)
    if update["cpu_stt"] and update["cpu_stt"] == update["gpu_stt"]:
        raise ValueError("CPU and GPU Wyoming providers must differ")
    return update


def save_settings_form(token, fields, available):
    """Save validated settings to the *existing* Supervisor managed App options."""
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    previous = load_options()
    changes = validate_settings_form(fields, previous, available)
    data = json.dumps({"options": {**previous, **changes}}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        SUPERVISOR_OPTIONS, data=data, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=8) as response:
        if response.status != 200:
            raise RuntimeError("TAFA App configuration could not be saved")
        reply = json.loads(response.read(16384))
    if reply.get("result") != "ok":
        raise RuntimeError("Supervisor rejected TAFA settings")
    return changes
