# Echo Relay Assist dashboard / Lovelace-Karte (v1.0.0)

Independent of the private Hauszentrale dashboard. Works with a Home Assistant dashboard and the Android Echo Relay command/status helper protocol. No changes to the APK. This is a developer preview; the three-state controller has been syntax- and state-transition-tested, not yet exercised on a clean HA instance or every Android WebView.

## Deutsch

1. Echo Relay installieren, mit HA verbinden und den Echo als Bluetooth-Medienausgang auswählen. Player starten. Das Mikrofon wird vom sichtbaren HA-Dashboard verwendet, nicht von der Relay-App.
2. Unter **Einstellungen → Geräte & Dienste → Helfer** zwei Text-Helfer mit maximal 255 Zeichen anlegen: `input_text.jarvis_native_audio_command` und `input_text.jarvis_native_audio_status`. Vorhandene Helfer wiederverwenden. Alternativ die [YAML-Vorlage](../homeassistant/templates/echo-relay-helpers.yaml) in die bestehende, korrekt konfigurierte packages-Struktur übernehmen; keine doppelten Definitionen.
3. [echo-relay-assist-card-v1.0.0.js](../homeassistant/www/jarvis/echo-relay-assist-card-v1.0.0.js) nach `/config/www/jarvis/` kopieren. Unter Einstellungen → Dashboards → Ressourcen als JavaScript-Modul eintragen: `/local/jarvis/echo-relay-assist-card-v1.0.0.js?v=1.0.0`.
4. Eine manuelle Karte in einem beliebigen Dashboard hinzufügen (Beispiel unten). Die bevorzugte Assist-Pipeline wird ohne Angabe verwendet. Wenn nötig eigene `pipeline_id` (STT/Intent/TTS) und `wake_pipeline_id` (Wakeword/STT) eintragen. Für Rufwortmodus ist ein konfigurierter serverseitiger Wakeword-Dienst erforderlich; ohne ihn Dauerbetrieb/Einmal sprechen verwenden.
5. Mikrofonberechtigung im HTTPS-Dashboard erteilen. Einmal drücken = Rufwort (grün), zweimal = Dauerbetrieb (blau), dreimal = aus. Beim Wechsel auf einen nicht sichtbaren Tab oder beim Entfernen der Karte stoppt sie. Kein automatischer Mikrofonstart nach Reload. Während der Antwort ist das Mikrofon geschlossen. Nach Sprechpausen oder Antworten hört der Dauerbetrieb erneut zu.
6. Im aufklappbaren Einstellungsbereich Echo Relay (Standard), Tablet/Bluetooth oder nativen Assist als Reserve wählen. Der Hauptbutton steuert immer den integrierten Assistenten. Der Android-Assistent wird als explizite Reserve geöffnet. Bei paralleler nativer Wakeword-Erkennung diese in der Companion App abschalten; optional `native_notify_service` mit passendem `mobile_app_...`-Dienst konfigurieren.
7. Nur eine aktive Karte/Bedienstelle pro Echo Relay Helper-Paar. Informiere Anwesende über die aktive Mikrofonaufnahme. Die App bestätigt die Audioausgabe; wie schnell das Streaming startet, hängt von der App-Version ab. Die Version 0.2.0 lädt vor Wiedergabe die vollständige Datei.

## English

1. Install Echo Relay on Android, pair the Echo using system Bluetooth settings, connect the app to HA and start its player.
2. Create two Text helpers (maximum 255 characters): `input_text.jarvis_native_audio_command` and `input_text.jarvis_native_audio_status`. Reuse existing helpers, or use the optional [YAML template](../homeassistant/templates/echo-relay-helpers.yaml) in a configured packages directory. Do not define them twice.
3. Copy [the card JavaScript](../homeassistant/www/jarvis/echo-relay-assist-card-v1.0.0.js) into `/config/www/jarvis/`, register `/local/jarvis/echo-relay-assist-card-v1.0.0.js?v=1.0.0` as a JavaScript module in Dashboard Resources and add a manual card.
4. Use your preferred HA Assist pipeline, or set your own pipeline IDs below. Wake-word mode needs a configured server-side wake-word engine. Continuous and one-shot modes do not require it. Use HTTPS and grant microphone access.
5. Tap the microphone: green wake word → blue continuous → off. It stops when hidden or disconnected and never starts automatically on reload; it pauses capture during playback and reopens for the next turn in continuous mode. Inform people nearby.
6. Settings contain Echo Relay (default), browser/tablet playback and explicit native Assist fallback. The main button always controls the dashboard assistant. Disable concurrent Companion App wake-word detection, or configure the optional `native_notify_service`. Use only one active controller per app/helper pair. Android version 0.2.0 downloads the whole audio file before playing; this card does not change the app.

```yaml
type: custom:echo-relay-assist-card
title: Echo Relay
# Optional / optional:
# pipeline_id: YOUR_ASSIST_PIPELINE_ID
# wake_pipeline_id: YOUR_WAKEWORD_PIPELINE_ID
# native_notify_service: mobile_app_your_tablet
# status_entity: input_text.your_optional_debug_status
# output: native_audio
```

The command/status entity names default to the app's fixed helper IDs. Only override `command_entity` and `relay_status_entity` if your Android client is configured to use the same pair. Optional direct Alexa fallback: configure both `alexa_script: your_script_service_name` (no script prefix) and `alexa_notify: notify.your_echo`. The script must accept `text` and `lautsprecher` fields. Direct Alexa may send audio via the Amazon cloud. Never use it for confidential replies. The browser card never stores HA access tokens; it uses the active authenticated HA connection.

## Changes / Änderungen

- v1.0.0: microphone cycle, explicit foreground capture, native Echo Relay status/command handling, settings and optional fallbacks. No private IDs or dependencies on Hauszentrale; English/German settings and main state labels. Detailed backend error text may be German or supplied by HA.
