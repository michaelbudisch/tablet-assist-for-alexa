"""TAFA Control Center, accessible tabbed presentation (no duplicated settings).

Only renders escaped text and trusted local markup from settings_ui.
All existing Supervisor App options and backend actions remain in server.py.
"""
import html


def render_dashboard(*, lang, version, default_tab, message, repo, csrf,
                     cards, picker, connection_panel, import_panel, devices_panel, checks, options, setup, pipeline, links, latest,
                     cache_info, note, install, retry_button, remove_button, mode):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    esc = lambda value: html.escape(str(value or ""), quote=True)
    allowed_tabs = ("overview", "connections", "setup", "devices", "maintenance")
    if default_tab not in allowed_tabs:
        default_tab = "overview"

    def status(key):
        names = {
            "needs_review":t("Prüfung nötig","Needs review"),
            "waiting":t("Einrichtung läuft","Setting up"),
            "ready":t("Bereit","Ready"), "reachable":t("Erreichbar","Reachable"),
            "selected":t("Eingerichtet","Configured"),
            "offline":t("Offline","Offline"),
            "busy":t("Beschäftigt","Busy"),
            "not_ready":t("Noch nicht bereit","Not ready"),
            "invalid":t("Ungültig","Invalid"),
            "missing":t("Nicht eingerichtet","Not configured"),
            "not_configured":t("Nicht eingerichtet","Not configured"),
            "unverified":t("Nicht gefunden","Not found"),
            "configured_unchecked":t("Eingetragen, ungeprüft","Set, not tested"),
            "unused":t("Nicht verwendet","Not in use"),
        }
        key = str(key or "missing")
        good = {"ready","reachable","selected"}
        bad = {"offline","invalid"}
        warn = {"busy","not_ready","unverified"}
        color = "good" if key in good else "bad" if key in bad else "warn" if key in warn else "neutral"
        return f'<span class="status-pill status-{color}"><span aria-hidden="true" class="status-dot"></span>{esc(names.get(key,key))}</span>'

    def summary_card(title, value, category="neutral"):
        return (f'<article class="metric"><div class="metric-label">{esc(title)}</div>'
                f'<strong>{esc(value)}</strong><div class="metric-footer">{status(category)}</div></article>')

    summary = "".join((
        summary_card(cards[0][0],cards[0][1],"selected" if "not installed" not in str(cards[0][1]) else "missing"),
        summary_card(cards[1][0],cards[1][1],"ready" if cards[1][1] == t("Bereit","Ready") else "not_ready"),
        summary_card(cards[2][0],cards[2][1],"neutral"),
        summary_card(cards[3][0],cards[3][1],"neutral"),
        summary_card(cards[4][0],cards[4][1],links.get("gpu")),
        summary_card("TAFA Lokal",t("Einsatzbereit","Ready") if pipeline.get("status")=="ready"
                     else t("Überprüfung erforderlich","Needs review") if pipeline.get("status")=="needs_review"
                     else t("Wird eingerichtet","Setting up"),
                     "ready" if pipeline.get("status")=="ready" else "not_ready"),
    ))
    expected_route = t("Tablet-Mikrofon → HA Assist (TAFA Lokal) → Tablet / Bluetooth",
                       "Tablet microphone → HA Assist (TAFA Lokal) → Tablet / Bluetooth")
    last_backend = (
        t("GPU-Whisper","GPU Whisper") if latest and latest.get("backend") == "zusatzrechner"
        else t("CPU / Homeserver","CPU / home server") if latest and latest.get("backend") == "homeserver"
        else t("Noch keine Daten","No recent reading"))
    duration = latest.get("duration_ms") if latest else None
    if isinstance(duration,(int,float)) and not isinstance(duration,bool):
        last_backend += f" · {round(duration)} ms"

    def endpoint(title, key, address, description):
        return (f'<article class="endpoint">'
                f'<div class="endpoint-title"><h3>{esc(title)}</h3>{status(checks.get(key))}</div>'
                f'<div class="endpoint-value">{esc(address) if address else esc(t("Nicht eingerichtet","Not configured"))}</div>'
                f'<p>{esc(description)}</p></article>')

    address = lambda key: str(options.get(key) or "")
    endpoints = "".join((
        endpoint("Piper", "external_piper_base",
                 t("Lokal in TAFA","Local in TAFA") if mode == "local" else address("external_piper_base"),
                 t("Piper-Sprachausgabe, bei Proxmox normalerweise Port 5000.","Piper speech, normally port 5000 on Proxmox.")),
        endpoint("Qwen · TTS", "gpu_base", address("gpu_base"),
                 t("GPU-Sprachausgabe, normalerweise Port 10502.","GPU speech, normally port 10502.")),
        endpoint("GPU Whisper · TCP 10300", "gpu_stt_host",
                 address("gpu_stt_host")+":10300" if address("gpu_stt_host") else "",
                 t("TCP-Prüfung; kein tatsächlicher Spracherkennungstest.","TCP check, not a real speech recognition test.")),
        endpoint("CPU Whisper · Wyoming", "cpu_stt", address("cpu_stt"),
                 t("CPU-STT-Entität für den Fallback.","CPU STT entity for fallback.")),
        endpoint("GPU Whisper · Wyoming", "gpu_stt", address("gpu_stt"),
                 t("In Home Assistant registrierte GPU-STT-Entität.","GPU STT entity registered in Home Assistant.")),
        endpoint("Ollama · Text-KI", "llm_agent", address("llm_agent"),
                 t("Ausgewählte HA-Konversationsentität; kein Live-Modelltest.","Selected HA conversation entity; no live model test.")),
        endpoint("Alexa · MP3", "mp3_base", address("mp3_base"),
                 t("Privater Generator; normalerweise Port 5001.","Private generator, normally port 5001.")),
        endpoint("Alexa · HTTPS", "public_audio_base", address("public_audio_base"),
                 t("Externer Audio-Endpunkt; aus Sicherheitsgründen nicht automatisch geprüft.","External audio endpoint; not probed automatically for safety.")),
    ))

    notice = f'<div class="notice" role="status">{esc(message)}</div>' if message else ""
    nav_items = [
        ("overview",t("Übersicht","Overview")),
        ("connections",t("Verbindungen","Connections")),
        ("setup",t("Einstellungen","Settings")),
        ("devices",t("Geräte & Multiroom","Devices & multiroom")),
        ("maintenance",t("Wartung & Hilfe","Maintenance & help")),
    ]
    nav = "".join(
        f'<a class="tab-link" href="#{key}" id="tab-{key}" role="tab" '
        f'aria-controls="{key}" aria-selected="false">{esc(title)}</a>'
        for key,title in nav_items
    )
    docs = "".join((
        f'<a href="{esc(repo)}/blob/main/docs/app.md" target="_blank" rel="noopener">Deutsch</a>',
        f'<a href="{esc(repo)}/blob/main/docs/en/app.md" target="_blank" rel="noopener">English</a>',
        f'<a href="{esc(repo)}/blob/main/docs/native-only.md" target="_blank" rel="noopener">Native Sprachsteuerung</a>',
        f'<a href="{esc(repo)}/blob/main/docs/en/native-only.md" target="_blank" rel="noopener">Native voice guide</a>',
        f'<a href="{esc(repo)}/tree/main/android" target="_blank" rel="noopener">Device Bridge</a>',
        f'<a href="{esc(repo)}/issues" target="_blank" rel="noopener">GitHub Issues</a>',
    ))
    return f"""<!doctype html>
<html lang="{lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark"><title>TAFA · Control Center</title>
<link rel="stylesheet" href="assets/control-center.css?v={version}">
<script src="assets/control-center.js?v={version}" defer></script>
</head>
<body data-default-tab="{default_tab}">
<div class="shell">
<header class="hero">
  <div class="hero-main">
    <div class="brand-mark" aria-hidden="true"><img src="assets/brand.svg?v={version}" alt="" width="54" height="54"></div>
    <div class="hero-text">
      <p class="eyebrow">TAFA Control Center</p>
      <h1>{t("TAFA – Verwaltung und Konfiguration","TAFA – Configuration and management")}</h1>
      <p>{t("Sprachassistent, Verbindungen und Geräte in Home Assistant verwalten.","Manage voice assistance, connections and devices in Home Assistant.")}</p>
    </div>
  </div>
  <div class="hero-actions">
    <span class="version-chip">v{version} · Beta</span>
    <div class="lang-switch" aria-label="{t("Sprache","Language")}">
      <a href="?lang=de" data-language-link{" aria-current='page'" if not en else ""}>DE</a>
      <a href="?lang=en" data-language-link{" aria-current='page'" if en else ""}>EN</a>
    </div>
  </div>
</header>
<nav class="tab-nav" role="tablist" aria-label="{t("Control-Center-Bereiche","Control Center sections")}">{nav}</nav>
{notice}
<main>
<section class="tab-panel" id="overview" role="tabpanel" aria-labelledby="tab-overview">
  <div class="section-heading">
    <p class="kicker">{t("SYSTEMSTATUS","SYSTEM STATUS")}</p>
    <h2>{t("Systemstatus","System status")}</h2>
    <p>{t("Status der eingerichteten Komponenten.","Status of configured components.")}</p>
  </div>
  <div class="route-card">
    <div><span class="route-caption">{t("Geplanter Sprachweg","Expected speech output route")}</span>
      <strong>{esc(expected_route)}</strong>
      <small>{t("Basierend auf den gespeicherten Einstellungen.","Based on stored configuration.")}</small></div>
    <div class="route-divider" aria-hidden="true"></div>
    <div><span class="route-caption">{t("Zuletzt verwendete Spracherkennung","Last speech recognition backend")}</span>
      <strong>{esc(last_backend)}</strong>
      <small>{t("Aus dem Home-Assistant-Sprachrouter, falls verfügbar.","From the Home Assistant speech router, if available.")}</small></div>
  </div>
  <div class="metric-grid">{summary}</div>
  <div class="assist-readiness" role="status">
    <div class="readiness-marker" aria-hidden="true">{"✓" if pipeline.get("status")=="ready" else "…"}</div>
    <div>
      <strong>{t("TAFA Lokal ist einsatzbereit","TAFA Lokal is ready") if pipeline.get("status")=="ready"
        else t("TAFA Lokal benötigt eine Prüfung","TAFA Lokal needs review") if pipeline.get("status")=="needs_review"
        else t("TAFA Lokal wird automatisch eingerichtet","TAFA Lokal is being configured")}</strong>
      <p>{esc(pipeline.get("detail",""))}</p>
      <p class="subtle">{t("Bestehende Standard-Sprachassistenten bleiben unverändert.","Existing default voice assistants are not changed.")}</p>
    </div>
    <a class="btn btn-outline" href="/config/voice-assistants" target="_top">{t("Sprachassistent auswählen","Select voice assistant")}</a>
  </div>
  <div class="shortcut-grid">
    <a href="#connections" class="shortcut"><span class="shortcut-icon" aria-hidden="true">01</span><strong>{t("Verbindungen","Connections")}</strong><small>{t("Serveradressen und JSON-Import","Server addresses and JSON import")}</small><span class="shortcut-go" aria-hidden="true">→</span></a>
    <a href="#setup" class="shortcut"><span class="shortcut-icon" aria-hidden="true">02</span><strong>{t("Einstellungen","Settings")}</strong><small>{t("Sprachverarbeitung und KI","Speech processing and AI")}</small><span class="shortcut-go" aria-hidden="true">→</span></a>
    <a href="#devices" class="shortcut"><span class="shortcut-icon" aria-hidden="true">03</span><strong>{t("Geräte & Multiroom","Devices & multiroom")}</strong><small>{t("Tablet- und Raumverwaltung","Tablet and room management")}</small><span class="shortcut-go" aria-hidden="true">→</span></a>
  </div>
</section>

<section class="tab-panel" id="connections" role="tabpanel" aria-labelledby="tab-connections">
  <div class="section-heading">
    <p class="kicker">{t("VERBINDUNGEN","CONNECTIONS")}</p>
    <h2>{t("Server und Komponenten verbinden","Connect servers and components")}</h2>
    <p>{t("Adressen bearbeiten, erreichbar prüfen und Proxmox-/GPU-Konfigurationen importieren.","Edit addresses, check connectivity and import Proxmox/GPU configuration files.")}</p>
  </div>
  {connection_panel}
  {import_panel}
</section>

<section class="tab-panel" id="setup" role="tabpanel" aria-labelledby="tab-setup">
  <div class="section-heading">
    <p class="kicker">{t("EINSTELLUNGEN","SETTINGS")}</p>
    <h2>{t("Sprachassistent und KI","Voice assistant and AI")}</h2>
    <p>{t("Sprachverarbeitung, KI und Ausgabeprofile. Netzwerkadressen stehen unter Verbindungen.","Speech processing, AI and voice profiles. Network addresses are under Connections.")}</p>
  </div>
  {picker}
</section>

<section class="tab-panel" id="devices" role="tabpanel" aria-labelledby="tab-devices">
  <div class="section-heading"><p class="kicker">{t("GERÄTE UND RÄUME","DEVICES AND ROOMS")}</p>
    <h2>{t("TAFA-Geräte und Räume","TAFA devices and rooms")}</h2>
    <p>{t("Tablet-Einstellungen, Multiroom und Raumverwaltung.","Tablet settings, multiroom and room management.")}</p>
  </div>
  {devices_panel}
</section>

<section class="tab-panel" id="maintenance" role="tabpanel" aria-labelledby="tab-maintenance">
  <div class="section-heading"><p class="kicker">{t("WARTUNG","MAINTENANCE")}</p>
    <h2>{t("Wartung & Hilfe","Maintenance & help")}</h2>
    <p>{t("Backend, Modelle und Dokumentation.","Backend, models and documentation.")}</p>
  </div>
  {('<div class="work-card"><h3>'+t("Einrichtung fortsetzen","Resume setup")+'</h3><p class="subtle">'+t("Die neue TAFA-Integration wurde gespeichert, aber Home Assistant Core muss sie einmal laden. Dein bestätigter JSON-Import wird anschließend automatisch abgeschlossen.","The new TAFA backend has been staged and HA Core needs one restart to load it. Your approved JSON import resumes automatically afterwards.")+'</p><form action="./" method="post"><input type="hidden" name="csrf" value="'+esc(csrf)+'"><input type="hidden" name="lang" value="'+lang+'"><input type="hidden" name="tab" value="maintenance"><label>'+t("Zur Bestätigung RESTART eingeben","Type RESTART to confirm")+'<input type="text" name="confirmation" required maxlength="7" pattern="RESTART"></label><button class="btn btn-primary" type="submit" name="action" value="restart_core">'+t("Home Assistant Core neu starten","Restart Home Assistant Core")+'</button></form></div>' if setup.get("status")=="awaiting_core_restart" else "")}
  <div class="maintenance-grid">
    <section class="work-card">
      <h3>{t("Einrichtungsstatus","Setup status")}</h3>
      <p class="setup-code">{esc(setup.get("status","pending"))}</p>
      <p class="subtle">{esc(message or setup.get("detail","") or note)}</p>
      <form action="./" method="post" class="action-form">
        <input type="hidden" name="csrf" value="{esc(csrf)}"><input type="hidden" name="lang" value="{lang}">
        <input type="hidden" name="tab" value="maintenance">
        <button class="btn btn-primary" name="action" value="backend" type="submit">{install}</button>
        {retry_button}
      </form>
    </section>
    <section class="work-card">
      <h3>{t("Lokale Sprachmodelle verwalten","Manage local speech models")}</h3>
      <p class="setup-code">{esc(cache_info)}</p>
      <p class="subtle">{t("Nur TAFA-eigene Piper-/Whisper-Dateien. Proxmox und Wyoming bleiben unberührt.","Only TAFA-owned Piper/Whisper files. Proxmox and Wyoming are untouched.")}</p>
      <p class="subtle">{t("Vor dem Löschen einen externen Sprachserver unter Einstellungen wählen und TAFA neu starten.","Before deleting, select an external speech server under Settings and restart TAFA.")}</p>
      {remove_button}
    </section>
  </div>
  <details class="support-disclosure"><summary>{t("Inbetriebnahme: 4 Schritte","Getting started: 4 steps")}</summary>
    <div class="support-body"><ol class="steps">
      <li>{t("TAFA installiert das Backend beim Start automatisch.","TAFA stages its backend automatically on startup.")}</li>
      <li>{t("Nach einem Backend-Update Home Assistant Core einmal neu starten.","Restart Home Assistant Core once after a backend update.")}</li>
      <li>{t("GPU-/Proxmox-JSON unter Verbindungen importieren. TAFA richtet Wyoming und Ollama ein, soweit verfügbar.","Import GPU/Proxmox JSON under Connections. TAFA configures Wyoming and Ollama when services are available.")}</li>
      <li>{t("TAFA Device Bridge für Rufwort und Audio verbinden.","Connect TAFA Device Bridge for wake words and audio.")}</li>
    </ol><a href="/config/integrations" target="_top">{t("Geräte & Dienste öffnen","Open Devices & services")}</a>
    <span aria-hidden="true"> · </span><a href="#devices">{t("Geräte &amp; Multiroom","Devices &amp; multiroom")}</a></div>
  </details>
  <section class="work-card support-links">
    <h3>{t("Dokumentation & Support","Documentation & support")}</h3>
    <div class="links">{docs}</div>
    <p class="subtle">{t("Dein privates Dashboard wird nicht installiert oder verändert.","Your private dashboard is not installed or modified.")}</p>
  </section>
</section>
</main>
<footer><span>TAFA <span aria-hidden="true">·</span> {version}</span>
  <span>{t("Konfiguration über Home Assistant","Configuration in Home Assistant")}</span></footer>
</div>
</body></html>"""
