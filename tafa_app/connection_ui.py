"""GPU-first, CPU-fallback, Alexa connection editor with Home Assistant STT choices.

Only edits App-owned options. No guessing or automatic swapping of Wyoming
providers, and no network calls occur while rendering this page.
"""
import html
import re

from speech_source import private_http_origin, setup_settings_values
from endpoint_checks import suggested_gpu_stt_host

CONNECTION_FIELDS = ("gpu_stt_host", "gpu_base", "gpu_stt", "llm_agent",
                     "external_piper_base", "cpu_stt", "mp3_base", "public_audio_base")
ADDRESS_FIELDS = frozenset(("gpu_stt_host", "gpu_base", "external_piper_base",
                            "mp3_base", "public_audio_base"))


def render_connection_form(options, lang, csrf, checks=None, wyoming=None,
                           wyoming_note="", latest=None):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    esc = lambda value: html.escape(str(value or ""), quote=True)
    options = options or {}
    checks = checks or {}
    wyoming = wyoming or []
    statuses = {
        "ready": t("Dienst bereit", "Service ready"),
        "reachable": t("Erreichbar – kein Spracherkennungstest", "Reachable – not a recognition test"),
        "not_ready": t("Erreichbar, nicht bereit", "Reachable, not ready"),
        "offline": t("Nicht erreichbar", "Unreachable"),
        "invalid": t("Ungültige Adresse", "Invalid address"),
        "selected": t("In Home Assistant gefunden", "Found in Home Assistant"),
        "unverified": t("Entität momentan nicht gefunden", "Entity not currently found"),
        "configured_unchecked": t("Eingetragen – ungeprüft", "Configured – not tested"),
        "unused": t("Momentan nicht verwendet", "Not currently used"),
        "missing": t("Nicht eingerichtet", "Not configured"),
    }

    def connection_field(key, label, placeholder, description):
        value = str(options.get(key) or "")
        suggested = False
        if key == "gpu_stt_host" and not value:
            value = suggested_gpu_stt_host(options.get("gpu_base", ""))
            suggested = bool(value)
        state = checks.get(key, "missing")
        return (
            '<div class="connection-field">'
            f'<label for="connection-{key}">{esc(label)}</label>'
            f'<input id="connection-{key}" name="{key}" type="text" '
            f'value="{esc(value)}" placeholder="{esc(placeholder)}" '
            f'data-connection-probe="{key}" maxlength="256" autocomplete="off" spellcheck="false">'
            f'<p class="field-help">{esc(description)}</p>'
            + (f'<p class="field-help">{t("IP aus Qwen-Adresse vorgeschlagen; vor dem Speichern prüfen.", "IP suggested from Qwen URL; verify before saving.")}</p>'
               if suggested else "")
            + f'<p class="probe-feedback" data-probe-result="{key}" role="status" aria-live="polite"'
            f' data-state="{esc(state)}">{esc(statuses.get(state, statuses["missing"]))}</p>'
            '</div>'
        )

    existing = {item.get("id") for item in wyoming if isinstance(item, dict)}
    def wyoming_field(key, label, description):
        selected = str(options.get(key) or "")
        rows = [f'<option value=""{" selected" if not selected else ""}>{t("Keine Auswahl", "Not selected")}</option>']
        for item in wyoming:
            identifier = item.get("id", "")
            if not isinstance(identifier, str) or not re.fullmatch(r"stt\.[a-z0-9_]+", identifier):
                continue
            name = item.get("name") or identifier
            label_text = name + " · " + identifier if name != identifier else identifier
            rows.append(f'<option value="{esc(identifier)}"{" selected" if selected == identifier else ""}>{esc(label_text)}</option>')
        if selected and selected not in existing:
            rows.append(f'<option value="{esc(selected)}" selected>{esc(selected)} · {t("momentan nicht gefunden", "currently unavailable")}</option>')
        state = checks.get(key, "missing")
        return (
            '<div class="connection-field">'
            f'<label for="connection-{key}">{esc(label)}</label>'
            f'<select id="connection-{key}" name="{key}">{"".join(rows)}</select>'
            f'<p class="field-help">{esc(description)}</p>'
            f'<p class="probe-feedback" data-state="{esc(state)}">{esc(statuses.get(state, statuses["missing"]))}</p>'
            '</div>'
        )

    def conversation_field():
        value = str(options.get("llm_agent") or "")
        return (
            '<div class="connection-field">'
            f'<label for="connection-llm_agent">{t("Text-KI: Home-Assistant-Gesprächsentität", "Text AI: Home Assistant conversation entity")}</label>'
            f'<input id="connection-llm_agent" type="text" name="llm_agent" value="{esc(value)}"'
            ' placeholder="conversation.ollama" maxlength="256" autocomplete="off" spellcheck="false">'
            f'<p class="field-help">{t("Zuerst Ollama oder einen anderen Gesprächsassistenten unter Geräte & Dienste einrichten. Hier die conversation.*-Entität eintragen.", "First configure Ollama or another conversation agent in HA Devices & services. Enter its conversation.* entity here.")}</p>'
            '</div>'
        )

    gpu = "".join((
        connection_field("gpu_stt_host",
            t("GPU-PC-IP – Schnellprüfung (Wyoming Port 10300)", "GPU PC IP – fast probe (Wyoming port 10300)"),
            "192.168.1.60",
            t("Vor der Spracherkennung prüft TAFA den GPU-Whisper-Port mit höchstens 0,8 Sekunden Wartezeit. Offline: direkte CPU-Ausweichroute. Dieser Eintrag ist keine Wyoming-Entität.", "Before recognition TAFA checks the GPU Whisper port with a 0.8 second timeout. If offline it falls back to CPU. This is not a Wyoming entity.")),
        connection_field("gpu_base",t("GPU / Qwen – Sprachausgabe (TTS)", "GPU / Qwen – speech synthesis (TTS)"),
            "http://192.168.1.60:10502",
            t("Adresse des Qwen-TTS-Workers mit Port 10502. Die Sprachausgabe prüft zusätzlich den Dienststatus.", "Qwen TTS worker URL including port 10502. Speech output also checks service readiness.")),
        wyoming_field("gpu_stt",t("GPU-Whisper – Wyoming-Entität", "GPU Whisper – Wyoming entity"),
            t("Aus Home Assistant auswählen; diese Entität führt die tatsächliche Spracherkennung aus.", "Choose from Home Assistant; this entity performs the actual speech recognition.")),
        conversation_field(),
    ))
    cpu = "".join((
        connection_field("external_piper_base",t("CPU / Proxmox – Piper-TTS", "CPU / Proxmox – Piper TTS"),
            "http://192.168.1.50:5000",
            t("Piper-Sprachausgabe des Proxmox-/CPU-Sprachservers, Port 5000.", "Piper speech synthesis on the Proxmox / CPU server, port 5000.")),
        wyoming_field("cpu_stt",t("CPU-Whisper – Wyoming-Entität (Fallback)", "CPU Whisper – Wyoming entity (fallback)"),
            t("Eigener CPU-Wyoming-Dienst. Muss sich von GPU-Whisper unterscheiden.", "Separate CPU Wyoming provider. Must differ from GPU Whisper.")),
    ))
    alexa = "".join((
        connection_field("mp3_base", t("Alexa – MP3-Generator", "Alexa – MP3 generator"),
            "http://192.168.1.50:5001",
            t("Lokaler MP3-Generator für optionale Alexa-Durchsagen.", "Local MP3 generator for optional Alexa announcements.")),
        connection_field("public_audio_base",t("Alexa – öffentliche HTTPS-Adresse", "Alexa – public HTTPS address"),
            "https://audio.example.org",
            t("Die Prüfung kontrolliert DNS und Zertifikat; ein tatsächlicher Amazon-Abruf wird damit nicht bestätigt.", "The check tests DNS and certificate; it does not prove Amazon can fetch an audio file.")),
    ))
    wyoming_note = wyoming_note or t(
        "Wyoming-Entitäten werden aus Home Assistant geladen. Falls keine angezeigt werden, zuerst Wyoming Protocol unter Geräte & Dienste installieren.",
        "Wyoming entities are loaded from Home Assistant. If none appear, install Wyoming Protocol under Devices & services.")
    recent = ""
    if latest and latest.get("backend") in ("homeserver", "zusatzrechner"):
        label = t("GPU-Whisper", "GPU Whisper") if latest["backend"] == "zusatzrechner" else t("CPU / Homeserver", "CPU / homeserver")
        milliseconds = latest.get("duration_ms")
        time = " · " + str(round(milliseconds)) + " ms" if isinstance(milliseconds, (int, float)) and not isinstance(milliseconds, bool) else ""
        recent = f'<p class="subtle">{t("Letzte Spracherkennung", "Last recognition")}: {esc(label+time)}</p>'
    return (
        '<section class="settings-card connection-editor">'
        f'<h2>{t("GPU / KI, CPU-Fallback und Alexa", "GPU / AI, CPU fallback and Alexa")}</h2>'
        f'<p>{t("Hier wählst du Server, GPU-Schnellprüfung und Home-Assistant-Entitäten. GPU wird bevorzugt, CPU dient als Reserve. IP und Wyoming-Entität haben unterschiedliche Aufgaben.", "Select services, the fast GPU check and Home Assistant entities. GPU is preferred; CPU is the backup. IP and Wyoming entity have different purposes.")}</p>'
        '<form id="tafa-connections" action="./" method="post">'
        f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
        f'<input type="hidden" name="lang" value="{esc(lang)}">'
        '<input type="hidden" name="tab" value="connections">'
        f'<div class="connection-group"><h3>{t("1 · GPU / KI – bevorzugter Weg", "1 · GPU / AI – preferred route")}</h3>'
        f'<div class="connection-grid">{gpu}</div></div>'
        f'<div class="connection-group"><h3>{t("2 · CPU-Fallback – Ersatzweg", "2 · CPU fallback – backup route")}</h3>'
        f'<div class="connection-grid">{cpu}</div></div>'
        f'<div class="connection-group"><h3>{t("3 · Alexa – optionale Durchsagen", "3 · Alexa – optional announcements")}</h3>'
        f'<div class="connection-grid">{alexa}</div></div>'
        f'<p class="subtle">{esc(wyoming_note)} <a href="/config/integrations" target="_top">{t("Wyoming in Home Assistant verwalten", "Manage Wyoming in Home Assistant")}</a></p>'
        + recent
        + f'<p class="subtle">{t("Ein offener Port bedeutet nicht, dass eine Spracherkennung funktioniert. Änderungen gelten erst nach dem Speichern.", "An open port does not prove speech recognition works. Changes take effect only after saving.")}</p>'
        f'<div class="form-actions"><span class="form-actions-note">{t("Alle anderen KI- und Raumoptionen bleiben erhalten.", "All unrelated AI and room settings remain unchanged.")}</span>'
        f'<button class="btn btn-primary" type="submit" name="action" value="connection_settings">{t("Verbindungen speichern", "Save connections")}</button></div>'
        '</form></section>'
    )


def validate_connection_form(fields, current, available=()):
    expected = frozenset(CONNECTION_FIELDS)
    if not expected.issubset(fields) or set(fields) - expected - {"csrf", "lang", "action", "tab"}:
        raise ValueError("Incomplete or unexpected connection settings")
    if any(len(parts) != 1 for parts in fields.values()):
        raise ValueError("Duplicate connection field")
    changes = {}
    for key in CONNECTION_FIELDS:
        value = fields[key][0]
        if not isinstance(value, str) or len(value) > 256:
            raise ValueError("Invalid connection value: " + key)
        value = value.strip()
        if key == "gpu_stt_host" and value:
            private_http_origin("http://" + value + ":10300")
        elif key in ("external_piper_base", "gpu_base", "mp3_base") and value:
            private_http_origin(value)
        changes[key] = value
    registered = {item.get("id") for item in available}
    for key in ("gpu_stt", "cpu_stt"):
        selected = changes[key]
        if selected and selected not in registered and selected != current.get(key, ""):
            raise ValueError("Wyoming entity not registered: " + key)
    if changes["gpu_stt"] and changes["gpu_stt"] == changes["cpu_stt"]:
        raise ValueError("GPU and CPU Wyoming entities must differ")
    if changes["llm_agent"] and not re.fullmatch(r"conversation\.[a-z0-9_]+", changes["llm_agent"]):
        raise ValueError("Invalid Home Assistant conversation entity")
    candidate = {**current, **changes}
    setup_settings_values(candidate)
    if candidate.get("speech_mode") == "external" and not candidate.get("external_piper_base"):
        raise ValueError("External CPU Piper requires an address")
    return changes
