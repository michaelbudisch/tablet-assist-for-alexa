"""Presentation for the TAFA native-bridge status and browser-only diagnosis."""
import html
import re



def public_device_snapshot(state):
    """Whitelist live Android status; never return HA users, room auth or tokens."""
    devices = []
    for item in state.get("devices", []):
        if not isinstance(item, dict):
            continue
        identifier = item.get("device_id", "")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-f0-9]{32}", identifier):
            continue
        observed = item.get("telemetry")
        if not isinstance(observed, dict):
            observed = {}
        telemetry = {}
        for key in ("wake_status", "microphone", "audio", "bluetooth", "app_version"):
            value = observed.get(key)
            if isinstance(value, str):
                telemetry[key] = value[:100]
        battery = observed.get("battery")
        if type(battery) is int and 0 <= battery <= 100:
            telemetry["battery"] = battery
        devices.append({
            "device_id": identifier,
            "room": str(item.get("room") or "Tablet")[:48],
            "online": item.get("online") is True,
            "muted": item.get("muted") is True,
            "word": str(item.get("word") or "")[:32],
            "telemetry": telemetry,
        })
    return {"devices": devices}


def render_voice_panel(lang, csrf, device_state):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    esc = lambda value: html.escape(str(value if value is not None else ""), quote=True)
    devices = public_device_snapshot(device_state)["devices"]
    choices = "".join(
        f'<option value="{esc(d["device_id"])}">{esc(d["room"])} · '
        f'{t("Online", "Online") if d["online"] else t("Offline", "Offline")}</option>'
        for d in devices
    )
    if not choices:
        choices = f'<option value="">{t("Kein verbundenes Tablet", "No enrolled tablet")}</option>'
    return f"""
<section class="tab-panel" id="voice" role="tabpanel" aria-labelledby="tab-voice">
  <div class="section-heading"><p class="kicker">{t("SPRACHSTEUERUNG", "VOICE CONTROL")}</p>
    <h2>{t("Jetzt sprechen", "Speak now")}</h2>
    <p>{t("Native TAFA Device Bridge steuern und den echten Sprachweg beobachten. Der Browser startet keine zusätzliche Rufworterkennung.",
          "Control the native TAFA Device Bridge and monitor the real speech route. The browser does not run a second wake-word detector.")}</p>
  </div>
  <div class="voice-board" id="tafa-voice-test" data-csrf="{esc(csrf)}" data-lang="{esc(lang)}">
    <section class="voice-box voice-mode-box">
      <div class="voice-box-heading"><h3>{t("TAFA Device Bridge · Mikrofon", "TAFA Device Bridge · microphone")}</h3>
        <span id="voice-native-indicator" class="voice-indicator">{t("Lade Gerätestatus", "Loading device status")}</span></div>
      <label for="voice-device-select">{t("Tablet auswählen", "Select tablet")}</label>
      <select id="voice-device-select" class="voice-device-select" aria-label="{t("Tablet auswählen", "Select tablet")}">{choices}</select>
      <div class="voice-modes" role="group" aria-label="{t("Native Mikrofoneinstellung für das ausgewählte Tablet", "Native microphone setting for selected tablet")}">
        <button type="button" data-native-mode="mute" aria-pressed="false">{t("Stumm", "Muted")}</button>
        <button type="button" data-native-mode="wake" aria-pressed="false">{t("Rufwort", "Wake word")}</button>
        <button type="button" data-native-mode="continuous" aria-pressed="false" disabled title="{t("Noch nicht von der Android-App unterstützt", "Not yet supported by the Android app")}">{t("Immer an", "Always on")}</button>
      </div>
      <p class="subtle">{t("Diese Schalter steuern die registrierte Android-App über Home Assistant. Die native Erkennung läuft auch bei geschlossenem Dashboard weiter.",
          "These switches control the enrolled Android app through Home Assistant. Native wake-word detection continues when the dashboard is closed.")}</p>
      <p class="subtle">{t("„Immer an“ ist in der aktuellen Device Bridge noch nicht implementiert. Die Option bleibt deaktiviert statt einen zusätzlichen Browser-Whisper-Dauerbetrieb zu starten.",
          "Always on is not implemented in the current Device Bridge. The option remains disabled instead of starting an extra browser Whisper loop.")}</p>
      <div class="voice-facts">
        <div><small>{t("Rufwort", "Wake phrase")}</small><strong id="voice-native-word">—</strong></div>
        <div><small>{t("Mikrofon / Erkennung", "Microphone / detection")}</small><strong id="voice-native-microphone">—</strong></div>
        <div><small>{t("Audioplayer", "Audio player")}</small><strong id="voice-native-audio">—</strong></div>
        <div><small>Bluetooth</small><strong id="voice-native-bluetooth">—</strong></div>
      </div>
      <p id="voice-native-status" class="voice-live" role="status" aria-live="polite">{t("Lade Gerätestatus", "Loading device status")}</p>
      <p class="subtle">{t("Status wird nur bei geöffneter Sprachsteuerungsseite aktualisiert. Die Android-App meldet Betriebsphasen, aber derzeit keine einzelnen End-to-End-Latenzen.",
         "Status refreshes only while this voice page is open. Android reports stages but not separate end-to-end latency measurements yet.")}</p>
    </section>

    <section class="voice-box">
      <div class="voice-box-heading"><h3>{t("Live-Sprachweg", "Live speech route")}</h3><span id="voice-pipeline" class="voice-quiet">TAFA Lokal</span></div>
      <div class="voice-route"><span>Android</span><span>→</span><span>Assist</span><span>→</span><span>Whisper</span><span>→</span><span>KI</span><span>→</span><span>Qwen/Piper</span><span>→</span><span>Bluetooth</span></div>
      <div class="voice-facts">
        <div><small>{t("Letzte STT-Quelle", "Last STT source")}</small><strong id="voice-stt-backend">—</strong></div>
        <div><small>{t("Letzte TTS-Quelle", "Last TTS source")}</small><strong id="voice-tts-backend">—</strong></div>
        <div><small>{t("Letzte STT-Dauer (HA)", "Last STT duration (HA)")}</small><strong id="voice-native-stt-time">—</strong></div>
        <div><small>{t("Erstes TTS-Audio (HA)", "First TTS audio (HA)")}</small><strong id="voice-time-first">—</strong></div>
      </div>
      <div class="voice-facts">
        <div><small>{t("STT-Entität", "STT entity")}</small><strong id="voice-stt-entity">—</strong></div>
        <div><small>{t("Gesprächsentität", "Conversation entity")}</small><strong id="voice-conv-entity">—</strong></div>
        <div><small>{t("TTS-Entität", "TTS entity")}</small><strong id="voice-tts-entity">—</strong></div>
        <div><small>{t("Letzter Browser-Testfehler", "Last browser test error")}</small><strong id="voice-error">—</strong></div>
      </div>
      <p class="subtle">{t("Das sind echte zuletzt gemeldete HA-Router-Werte, nicht erfundene Gesamtzeiten des Android-Players.",
          "These are actual latest HA router values, not estimated total Android playback timings.")}</p>
    </section>

    <section class="voice-box">
      <div class="voice-box-heading"><h3>{t("Browser-Diagnose (optional)", "Browser diagnostics (optional)")}</h3>
        <span id="voice-mic-indicator" class="voice-indicator">{t("Mikrofon aus", "Mic off")}</span></div>
      <p class="subtle">{t("„Einmal sprechen“ nimmt nur einmal im Browser auf. Es verändert die Android-Mikrofoneinstellungen nicht und spielt Antworten ausschließlich im Browser ab.",
          "Speak once records one sample in this browser. It does not change Android microphone settings, and plays replies in the browser only.")}</p>
      <div class="voice-actions">
        <button type="button" id="voice-once" class="btn btn-primary">🎙 {t("Einmal sprechen", "Speak once")}</button>
        <button type="button" id="voice-stop" class="btn btn-outline">{t("Aufnahme stoppen", "Stop recording")}</button>
        <button type="button" id="voice-refresh" class="btn btn-outline">{t("Status aktualisieren", "Refresh status")}</button>
      </div>
      <p id="voice-live" class="voice-live" role="status" aria-live="polite">{t("Bereit · Browser-Mikrofon aus", "Ready · browser microphone off")}</p>
      <p class="subtle">{t("Browser-Testphase:", "Browser test stage:")} <span id="voice-phase">—</span></p>
    </section>

    <section class="voice-box voice-history">
      <div class="voice-box-heading"><h3>{t("Gesprächsprotokoll","Conversation log")}</h3>
        <button class="btn btn-outline" id="voice-clear" type="button">{t("Protokoll leeren","Clear log")}</button></div>
      <p class="subtle">{t("Nur manuelle Browser-Testgespräche dieser geöffneten Seite. Native Android-Unterhaltungen werden nicht gespeichert.",
        "Only manual browser test conversations on this open page. Native Android conversations are not stored.")}</p>
      <div id="voice-history-list" class="voice-history-list" role="log" aria-live="polite">
        <p class="subtle" id="voice-history-empty">{t("Noch keine Testgespräche.","No test conversations yet.")}</p>
      </div>
      <form id="voice-text-form" class="voice-text-form">
        <label for="voice-text-input">{t("Testfrage ohne Mikrofon","Test question without microphone")}</label>
        <div><input type="text" id="voice-text-input" maxlength="300" placeholder="{t("Kurze Frage an TAFA Lokal","Short question for TAFA Lokal")}" required>
        <button class="btn btn-primary" type="submit">{t("Text testen","Test text")}</button></div>
      </form>
      <div class="voice-actions"><button id="voice-replay" type="button" class="btn btn-outline" disabled>{t("Letzte Audioantwort abspielen","Replay latest audio")}</button></div>
    </section>


    <section class="voice-box">
      <div class="voice-box-heading"><h3>{t("Browser-Testzeiten","Browser test timings")}</h3><span class="voice-quiet">{t("Letzter manueller Test","Latest manual test")}</span></div>
      <div class="voice-timings">
        <div><small>{t("Aufnahme","Recording")}</small><strong id="voice-time-capture">—</strong></div>
        <div><small>{t("Spracherkennung (STT)","Speech recognition (STT)")}</small><strong id="voice-time-stt">—</strong></div>
        <div><small>{t("Mikrofon bis Text","Microphone to text")}</small><strong id="voice-time-audio">—</strong></div>
        <div><small>{t("KI/Gespräch","AI/conversation")}</small><strong id="voice-time-intent">—</strong></div>
        <div><small>{t("Sprachausgabe (TTS)","Speech output (TTS)")}</small><strong id="voice-time-tts">—</strong></div>
        <div><small>{t("Erstes Audio (HA-Wert)","First audio (HA value)")}</small><strong id="voice-time-first">—</strong></div>
        <div><small>{t("Gesamtdauer","Total duration")}</small><strong id="voice-time-total">—</strong></div>
        <div><small>{t("Ø letzte 5 Tests","Average last 5 tests")}</small><strong id="voice-time-average">—</strong></div>
      </div>
      <p class="subtle">{t("Nur tatsächlich gemessene Werte. Die Gesamtdauer umfasst den Assist-Lauf nach Aufnahmeende; Aufnahme und Browser-Wiedergabe werden getrennt ausgewiesen. Nicht verfügbare Messwerte bleiben leer.",
        "Only measured values. Total duration covers the Assist run after recording; capture and browser playback are separate. Unavailable metrics remain blank.")}</p>
    </section>
  </div>
</section>
"""

  </div>
</section>
"""
