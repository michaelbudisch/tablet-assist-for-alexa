"""One admin-only settings editor for the Supervisor-managed TAFA App options.

The native HA App Configuration and this UI share /data/options.json. Changes are
validated before storing and require a TAFA App restart to apply. No second store.
"""
import html
import json
import urllib.request

from speech_source import load_options, load_supervisor_options, private_http_origin, setup_settings_values
from endpoint_checks import suggested_gpu_stt_host
from connection_ui import render_connection_form, validate_connection_form, CONNECTION_FIELDS, ADDRESS_FIELDS
from wyoming_picker import SUPERVISOR_OPTIONS

CHOICES = {
    "speech_mode": ("setup", "local", "external"),
    "hardware_profile": ("automatic", "cpu"),
    "voice_variant": ("default", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
    "live_profile": ("natural", "studio", "clear"),
    "conversation_mode": ("intelligent", "automatic", "manual"),
    "mp3_profile": ("natural", "studio", "announcement"),
}
TEXT_FIELDS = (
    "external_piper_base", "gpu_base", "gpu_stt_host", "llm_agent",
    "mp3_base", "public_audio_base", "rooms_json", "sources_json",
    "reminder_room", "cpu_stt", "gpu_stt", "search_base",
    "family_name_man", "family_name_woman", "family_name_child",
)
BOOL_FIELDS = ("chime", "learning_enabled", "reminders_enabled")
FORM_FIELDS = frozenset((*CHOICES, *TEXT_FIELDS, *BOOL_FIELDS))
ROUTING_FIELDS = frozenset(("cpu_stt", "gpu_stt", "llm_agent"))
SETTINGS_FIELDS = FORM_FIELDS - ADDRESS_FIELDS - ROUTING_FIELDS - frozenset(("sources_json", "rooms_json"))


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
        return f'<div class="field"><label for="{name}">{label}</label>{control}' + (f'<p class="field-help">{hint}</p>' if hint else "") + status_line(name) + "</div>"

    def select(name, label, entries, selected=None):
        selected = _value(options, name) if selected is None else selected
        choices = []
        for value, title in entries:
            choices.append(f'<option value="{esc(value)}"{" selected" if selected == value else ""}>{esc(title)}</option>')
        return f'<div class="field"><label for="{name}">{label}</label><select name="{name}" id="{name}">{"".join(choices)}</select>' + status_line(name) + "</div>"

    def check(name, label):
        return (f'<label class="toggle"><input type="checkbox" name="{name}" value="1"'
                f'{" checked" if options.get(name) is True else ""}> {label}</label>')

    return f"""
<section id="tafa-settings" class="settings-card">
<h2>{t("Sprachassistent und KI", "Voice assistant and AI")}</h2>
<p>{t("Sprachverarbeitung, KI-Auswahl und Verhalten. Serveradressen und JSON-Import findest du unter Verbindungen.",
"Configure speech, AI and behavior here. Service addresses and JSON import are under Connections.")}</p>
<form action="./" method="post">
<input type="hidden" name="csrf" value="{esc(csrf)}">
<input type="hidden" name="lang" value="{esc(lang)}"><input type="hidden" name="tab" value="setup">
<details open><summary>1 · {t("GPU und CPU – Ausgabe und Fallback", "GPU and CPU – output and fallback")}</summary>
{select("speech_mode",t("Wo läuft Piper?", "Where does Piper run?"),
 [("setup",t("Einrichtung: zunächst keinen Sprachserver starten", "Setup: do not start speech yet")),
  ("local",t("In der TAFA-App (mit CPU-Fallback)", "Inside TAFA (CPU fallback)")),
  ("external",t("Extern auf Proxmox", "External Proxmox server"))])}
{select("hardware_profile",t("Sprachausgabe", "Speech output"),
 [("automatic",t("GPU/Qwen bevorzugen; bei Ausfall Piper", "Prefer GPU Qwen; use Piper on failure")),
  ("cpu",t("Nur Piper/CPU verwenden", "Use only Piper/CPU"))])}
<p class="muted">{t("GPU-IP und CPU-/GPU-Wyoming-Entitäten findest du gesammelt unter Verbindungen. Die GPU-IP ist nur eine schnelle Vorprüfung, Wyoming übernimmt die Spracherkennung.", "GPU IP and CPU/GPU Wyoming entities are grouped under Connections. The IP is a fast precheck; Wyoming handles recognition.")}</p>
</details>
<details><summary>2 · {t("KI und Gesprächsverhalten", "AI and conversation behavior")}</summary>
{select("conversation_mode",t("Gesprächsverhalten", "Conversation behavior"),
 [("intelligent",t("Intelligent (empfohlen)", "Intelligent (recommended)")),
  ("automatic",t("Automatisch", "Automatic")),("manual",t("Manuell", "Manual"))])}
<p class="muted">{t("Intelligent: Nur nach einer echten Rückfrage weitersprechen. Automatisch: Nach jeder Antwort ein begrenztes Anschlussfenster. Manuell: Nach gewöhnlichen Antworten wieder Rufwort erwarten; explizite Dialoge (z. B. Suchtreffer wählen) bleiben möglich. Anzahl und Wartezeit stellst du zusätzlich lokal in der TAFA Device Bridge ein. Den KI-Gesprächsassistenten wählst du unter Verbindungen.", "Intelligent: Follow up only when TAFA explicitly requests an answer. Automatic: Allow a bounded listening window after every answer. Manual: Wake word again after ordinary replies; explicit dialogs (such as choosing search results) remain available. The tablet also controls its own maximum and listening time. Configure the LLM conversation agent under Connections.")}</p>
</details>
<details><summary>3 · {t("Stimme und Klang", "Voice and sound")}</summary>
{select("voice_variant",t("Qwen-Stimmvariante", "Qwen voice variant"),
 [(i,t("Standard", "Default") if i == "default" else i) for i in CHOICES["voice_variant"]])}
{select("live_profile",t("Klangprofil", "Sound profile"),
 [(i,i.title()) for i in CHOICES["live_profile"]])}
</details>
<details><summary>4 · {t("Alexa-Durchsagen (optional)", "Alexa announcements (optional)")}</summary>
{select("mp3_profile",t("Durchsage-Klang", "Announcement sound"),[(i,i.title()) for i in CHOICES["mp3_profile"]])}
{check("chime",t("Hinweiston verwenden", "Use chime"))}
<p class="muted">{t("Alexa-Ausgaberäume und Benachrichtigungen unter Funktionen & Datenquellen zuordnen.", "Assign Alexa output rooms and notification services under Features & sources.")}</p>
</details>
<details><summary>5 · {t("Erweiterungen", "Extensions")}</summary>
<p class="muted">{t("Sensoren lassen sich über den Reiter Funktionen & Datenquellen ohne JSON zuordnen.", "Configure sensors without JSON in the Features & sources tab.")}</p>
{field("search_base",t("SearXNG-Adresse (optional, z. B. http://192.168.1.50:8888)", "SearXNG server (optional, e.g. http://192.168.1.50:8888)"))}
<p class="muted">{t("Internetsuche wird nur bei einer ausdrücklichen Suchanfrage verwendet. Ohne SearXNG bleiben alle anderen Funktionen aktiv.", "Internet search runs only for explicit queries. Everything else works without SearXNG.")}</p>
{check("learning_enabled",t("Lernfunktionen aktivieren", "Enable learning features"))}
{check("reminders_enabled",t("Erinnerungen aktivieren", "Enable reminders"))}
{field("reminder_room",t("Erinnerungsraum (wenn eingerichtet)", "Reminder room (if configured)"))}
</details>
<details><summary>6 · {t("Familie & Begrüßung", "Family & greetings")}</summary>
{field("family_name_man",t("Name Person 1", "Person 1 name"))}
{field("family_name_woman",t("Name Person 2", "Person 2 name"))}
{field("family_name_child",t("Name Kind (optional)", "Child name (optional)"))}
<p class="muted">{t("Namen werden zentral in TAFA gespeichert; bestehende Begrüßungsregeln bleiben erhalten.", "Names are stored centrally in TAFA; existing greeting rules remain unchanged.")}</p>
</details>
<p class="muted">{t("Die Felder werden geprüft und andere TAFA-Einstellungen bleiben erhalten. Änderungen werden automatisch übernommen; ein neu installiertes HA-Backend kann einen Core-Neustart erfordern.",
"Fields are checked and unrelated TAFA settings are preserved. Changes apply automatically; a new HA backend may require a Core restart.")}</p>
<div class="form-actions"><span class="form-actions-note">{t("Änderungen werden automatisch übernommen", "Changes are applied automatically")}</span><button class="btn btn-primary" type="submit" name="action" value="settings">{t("Einstellungen speichern", "Save settings")}</button></div>
</form></section>
"""



def save_connection_form(token, fields, available=()):
    """Store only Connection form fields in existing Supervisor App options."""
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    current = load_supervisor_options(token)
    changes = validate_connection_form(fields, current, available)
    return save_app_changes(token, changes)


def validate_settings_form(fields, current, available):
    """Require the complete editor submission; preserve unrelated App keys."""
    required = SETTINGS_FIELDS - set(BOOL_FIELDS)
    if not required.issubset(fields):
        raise ValueError("Incomplete TAFA settings form")
    if set(fields) - SETTINGS_FIELDS - {"csrf", "lang", "action", "tab"}:
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
    candidate = {**current, **update}
    if update["speech_mode"] == "external":
        private_http_origin(candidate.get("external_piper_base", ""))
    setup_settings_values(candidate)
    return update


def save_settings_form(token, fields, available):
    """Save validated settings to the *existing* Supervisor managed App options."""
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    previous = load_supervisor_options(token)
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
    # A 200 response is not enough: verify the canonical persisted settings
    # before reporting success or handing a snapshot to Home Assistant.
    confirmed = load_supervisor_options(token)
    if any(confirmed.get(key) != value for key, value in changes.items()):
        raise RuntimeError("TAFA settings were not persisted as requested")
    return confirmed


def save_app_changes(token,changes,*,import_kind=None):
    """Persist validated import changes to the one Supervisor App option store."""
    if not token:
        raise RuntimeError("Supervisor authentication unavailable")
    if not isinstance(changes,dict):
        raise ValueError("Invalid import options")
    current=load_supervisor_options(token)
    if import_kind is not None:
        # The Supervisor store may have changed since the JSON preview or
        # provisioning step. Reconcile again against its ACTUAL last-read
        # values, not a previous snapshot. Only a user-confirmed worker/CT
        # import may clear an opposite-role duplicate; manual settings retain
        # the stricter duplicate validation.
        from import_manifest import reconcile_imported_stt
        changes=reconcile_imported_stt(current,changes,import_kind)
    proposed={**current,**changes}
    setup_settings_values(proposed)
    data=json.dumps({"options":proposed},ensure_ascii=False).encode("utf-8")
    req=urllib.request.Request(
        SUPERVISOR_OPTIONS,data=data,method="POST",
        headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=8) as response:
        if response.status!=200 or json.loads(response.read(16384)).get("result")!="ok":
            raise RuntimeError("Supervisor did not accept import settings")
    confirmed = load_supervisor_options(token)
    if any(confirmed.get(key) != value for key, value in changes.items()):
        raise RuntimeError("TAFA App options were not persisted as requested")
    return changes
