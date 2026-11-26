"""Presentation for the dedicated TAFA speech-test area."""
import html
import re


def render_voice_panel(lang, csrf, device_state):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    esc = lambda v: html.escape(str(v or ""), quote=True)
    devices = []
    for item in device_state.get("devices", []):
        if not isinstance(item, dict) or not re.fullmatch(r"[a-f0-9]{32}", str(item.get("device_id") or "")):
            continue
        room = str(item.get("room") or "Tablet")[:48]
        status = t("online", "online") if item.get("online") else "offline"
        muted = t("stumm", "muted") if item.get("muted") else t("aktiv", "active")
        devices.append('<li><strong>' + esc(room) + '</strong> · ' + esc(status) + ' · ' +
                       t("App-Mikrofon: ", "App mic: ") + esc(muted) + '</li>')
    if not devices:
        devices.append('<li>' + t("Keine angemeldeten Tablets gefunden.", "No enrolled tablets found.") + '</li>')
    return f"""
<section class="tab-panel" id="voice" role="tabpanel" aria-labelledby="tab-voice">
  <div class="section-heading"><p class="kicker">{t("SPRACHTEST","VOICE TEST")}</p>
    <h2>{t("Jetzt sprechen","Speak now")}</h2>
    <p>{t("TAFA Lokal testen, Gesprächsverlauf ansehen und tatsächliche Reaktionszeiten prüfen.",
          "Test TAFA Lokal, review conversations and inspect real response timings.")}</p>
  </div>
  <div class="voice-board" id="tafa-voice-test" data-csrf="{esc(csrf)}" data-lang="{esc(lang)}">
    <section class="voice-box voice-mode-box">
      <div class="voice-box-heading"><h3>{t("Sprachmodus","Voice mode")}</h3><span id="voice-mic-indicator" class="voice-indicator">{t("Mikrofon aus","Mic off")}</span></div>
      <div class="voice-modes" role="group" aria-label="{t("Mikrofonmodus dieser Seite","Microphone mode on this page")}">
        <button type="button" data-voice-mode="mute" aria-pressed="true">{t("Stumm","Muted")}</button>
        <button type="button" data-voice-mode="wake" aria-pressed="false">{t("Rufwort","Wake word")}</button>
        <button type="button" data-voice-mode="continuous" aria-pressed="false">{t("Immer an","Always on")}</button>
      </div>
      <p class="subtle">{t("Diese Modi gelten nur für das Mikrofon dieser geöffneten Seite. Beim Verlassen oder Ausblenden endet die Aufnahme. Die Android-App bleibt unverändert.",
          "These modes only affect the microphone of this open page. Recording stops when the page is hidden or left. Android settings stay unchanged.")}</p>
      <p class="subtle">{t("Rufwort wird hier über Whisper erkannt (z. B. „Jarvis“), nicht über die native Android-Wakeword-Engine. Die Erkennung benötigt den TAFA-Sprachweg.",
          "Wake phrases are recognized here using Whisper (e.g. Jarvis), not the native Android wake-word engine. TAFA speech recognition must be available.")}</p>
      <div class="voice-actions">
        <button type="button" id="voice-once" class="btn btn-primary">🎙 {t("Einmal sprechen","Speak once")}</button>
        <button type="button" id="voice-stop" class="btn btn-outline">{t("Aufnahme stoppen","Stop recording")}</button>
        <button type="button" id="voice-refresh" class="btn btn-outline">{t("Diagnose aktualisieren","Refresh diagnostics")}</button>
      </div>
      <p id="voice-live" class="voice-live" role="status" aria-live="polite">{t("Bereit · Mikrofon ausgeschaltet","Ready · microphone off")}</p>
    </section>

    <section class="voice-box">
      <div class="voice-box-heading"><h3>{t("Live-Sprachweg","Live route")}</h3><span id="voice-pipeline" class="voice-quiet">TAFA Lokal</span></div>
      <div class="voice-route"><span>{t("Browser-Mikrofon","Browser microphone")}</span><span>→</span><span>Whisper</span><span>→</span><span>TAFA</span><span>→</span><span>Qwen/Piper</span></div>
      <div class="voice-facts">
        <div><small>{t("Phase","Phase")}</small><strong id="voice-phase">—</strong></div>
        <div><small>STT</small><strong id="voice-stt-backend">—</strong></div>
        <div><small>TTS</small><strong id="voice-tts-backend">—</strong></div>
        <div><small>{t("Ausgabe","Output")}</small><strong>{t("Browser-Lautsprecher","Browser speaker")}</strong></div>
      </div>
      <div class="voice-facts">
        <div><small>{t("STT-Entität","STT entity")}</small><strong id="voice-stt-entity">—</strong></div>
        <div><small>{t("Gesprächsentität","Conversation entity")}</small><strong id="voice-conv-entity">—</strong></div>
        <div><small>{t("TTS-Entität","TTS entity")}</small><strong id="voice-tts-entity">—</strong></div>
        <div><small>{t("Letzter Fehler","Last error")}</small><strong id="voice-error">—</strong></div>
      </div>
      <details class="voice-device-info"><summary>{t("Tablets und Ausgabegeräte (Status)","Tablets and output devices (status)")}</summary>
        <p class="subtle">{t("Nur Anzeige. Der Sprachtest spielt auf diesem Browser ab; die Tablet-/Alexa-Ausgabe wird hier nicht umgestellt.",
          "Read-only. Speech tests play in this browser; tablet/Alexa output is not changed here.")}</p><ul>{"".join(devices)}</ul>
      </details>
    </section>

    <section class="voice-box voice-history">
      <div class="voice-box-heading"><h3>{t("Gesprächsprotokoll","Conversation log")}</h3>
        <button class="btn btn-outline" id="voice-clear" type="button">{t("Protokoll leeren","Clear log")}</button></div>
      <p class="subtle">{t("Nur während dieser geöffneten Seite im Browser gespeichert. Keine dauerhafte Speicherung von Sprachaufnahmen oder Transkripten.",
        "Stored only in this open browser page. No persistent recording or transcript storage.")}</p>
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
      <div class="voice-box-heading"><h3>{t("Zeiten und Diagnose","Timings and diagnostics")}</h3><span class="voice-quiet">{t("Letzter Test","Latest test")}</span></div>
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
