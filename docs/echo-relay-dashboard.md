# Echo Relay Assist dashboard / Lovelace-Karte (v1.0.3)

Independent of the private Hauszentrale dashboard. Works with a Home Assistant dashboard and the Android Echo Relay command/status helper protocol. No changes to the APK. This is a developer preview; the three-state controller has been syntax- and state-transition-tested, not yet exercised on a clean HA instance or every Android WebView.

## Deutsch

1. Echo Relay installieren, mit HA verbinden und den Echo als Bluetooth-Medienausgang auswählen. Player starten. Das Mikrofon wird vom sichtbaren HA-Dashboard verwendet, nicht von der Relay-App.
2. Unter **Einstellungen → Geräte & Dienste → Helfer** zwei Text-Helfer mit maximal 255 Zeichen anlegen: `input_text.jarvis_native_audio_command` und `input_text.jarvis_native_audio_status`. Vorhandene Helfer wiederverwenden. Alternativ die [YAML-Vorlage](../homeassistant/templates/echo-relay-helpers.yaml) in die bestehende, korrekt konfigurierte packages-Struktur übernehmen; keine doppelten Definitionen.
3. Auch [jarvis-camera-preview-v1.1.0.js](../homeassistant/www/jarvis/jarvis-camera-preview-v1.1.0.js) nach `/config/www/jarvis/` kopieren (dynamischer Import, kein eigener Ressourceneintrag). [echo-relay-assist-card-v1.0.3.js](../homeassistant/www/jarvis/echo-relay-assist-card-v1.0.3.js) nach `/config/www/jarvis/` kopieren. Unter Einstellungen → Dashboards → Ressourcen als JavaScript-Modul eintragen: `/local/jarvis/echo-relay-assist-card-v1.0.3.js?v=1.0.3`.
4. Eine manuelle Karte in einem beliebigen Dashboard hinzufügen (Beispiel unten). Die bevorzugte Assist-Pipeline wird ohne Angabe verwendet. Wenn nötig eigene `pipeline_id` (STT/Intent/TTS) und `wake_pipeline_id` (Wakeword/STT) eintragen. Für Rufwortmodus ist ein konfigurierter serverseitiger Wakeword-Dienst erforderlich; ohne ihn Dauerbetrieb/Einmal sprechen verwenden.
5. Mikrofonberechtigung im HTTPS-Dashboard erteilen. Einmal drücken = Rufwort (grün), zweimal = Dauerbetrieb (blau), dreimal = aus. Beim Wechsel auf einen nicht sichtbaren Tab oder beim Entfernen der Karte stoppt sie. Kein automatischer Mikrofonstart nach Reload. Während der Antwort ist das Mikrofon geschlossen. Nach Sprechpausen oder Antworten hört der Dauerbetrieb erneut zu.
6. Im aufklappbaren Einstellungsbereich Echo Relay (Standard), Tablet/Bluetooth oder nativen Assist als Reserve wählen. Der Hauptbutton steuert immer den integrierten Assistenten. Der Android-Assistent wird als explizite Reserve geöffnet. Bei paralleler nativer Wakeword-Erkennung diese in der Companion App abschalten; optional `native_notify_service` mit passendem `mobile_app_...`-Dienst konfigurieren.
7. Nur eine aktive Karte/Bedienstelle pro Echo Relay Helper-Paar. Informiere Anwesende über die aktive Mikrofonaufnahme. Die App bestätigt die Audioausgabe; wie schnell das Streaming startet, hängt von der App-Version ab. Ab App-Version 0.3.0 werden MP3 und PCM/WAV fortlaufend mit kleinem Anfangspuffer abgespielt; Version 0.2.0 lädt noch die vollständige Datei.

## English

1. Install Echo Relay on Android, pair the Echo using system Bluetooth settings, connect the app to HA and start its player.
2. Create two Text helpers (maximum 255 characters): `input_text.jarvis_native_audio_command` and `input_text.jarvis_native_audio_status`. Reuse existing helpers, or use the optional [YAML template](../homeassistant/templates/echo-relay-helpers.yaml) in a configured packages directory. Do not define them twice.
3. Copy [jarvis-camera-preview-v1.1.0.js](../homeassistant/www/jarvis/jarvis-camera-preview-v1.1.0.js) into `/config/www/jarvis/` too (dynamically imported; no separate resource entry). Copy [the card JavaScript](../homeassistant/www/jarvis/echo-relay-assist-card-v1.0.3.js) into `/config/www/jarvis/`, register `/local/jarvis/echo-relay-assist-card-v1.0.3.js?v=1.0.3` as a JavaScript module in Dashboard Resources and add a manual card.
4. Use your preferred HA Assist pipeline, or set your own pipeline IDs below. Wake-word mode needs a configured server-side wake-word engine. Continuous and one-shot modes do not require it. Use HTTPS and grant microphone access.
5. Tap the microphone: green wake word → blue continuous → off. It stops when hidden or disconnected and never starts automatically on reload; it pauses capture during playback and reopens for the next turn in continuous mode. Inform people nearby.
6. Settings contain Echo Relay (default), browser/tablet playback and explicit native Assist fallback. The main button always controls the dashboard assistant. Disable concurrent Companion App wake-word detection, or configure the optional `native_notify_service`. Use only one active controller per app/helper pair. Android app 0.3.0 streams MP3/PCM WAV with a small startup buffer; 0.2.0 still downloads the whole file. The card does not update the APK.

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

## Camera questions / Kamerafragen

Mit **Jarvis Tablet Audio 1.4.3** und **GPU Worker 1.7.0**: Außen-/Haustürkamera in den Integrationsoptionen auswählen. Fragen wie „Wer ist an der Haustür?“, „Was ist an der Haustür?“ und „Was ist draußen los?“ öffnen die zugeordnete Kamera in einer Jarvis-Kamera-Infobox im anfragenden, sichtbaren Dashboard. Gleichzeitig beschreibt Jarvis das abgerufene Einzelbild. Personen werden nur anhand sichtbarer Merkmale wie Kleidung oder mitgeführter Gegenstände beschrieben; keine Namenszuordnung oder Gesichtserkennung. Die Infobox startet die Liveansicht stumm, während die Beschreibung ein Einzelbild betrifft. Alle Bildbeschreibungen können falsch sein.

With Jarvis Tablet Audio 1.4.3 and GPU Worker 1.7.0, configured door/outdoor/tablet camera questions open the corresponding Jarvis camera infobox only on the requesting visible dashboard. Jarvis describes a snapshot, including generic visible people, clothing and carried objects, without identity recognition. The dialog automatically starts a muted live view; the description remains a single-image observation and may be wrong. Other devices, hidden dashboards and native Companion Assist do not automatically open this dialog. Ordinary door controls retain their existing route. A failed preview never interrupts the spoken response.

App **0.5.0** continues to work; no APK update is required. Copy both JavaScript files, update the card resource, restart HA after the backend update, then reload the dashboard. This also applies to the separately maintained Hauszentrale Kiosk controller when its preview hook is installed.

## Changes / Änderungen

- v1.0.3: auto-started muted live camera infobox, speech-end countdown, stream cleanup and one-time extension.

- v1.0.2: configured camera preview for camera questions, restricted to the active requesting dashboard; shared backend mapping and read permissions.

- v1.0.1: wake-word and speech detection, processing/buffering and playback indicators (DE/EN). Speech detection indicates voiced audio, not speaker identity.

- v1.0.0: microphone cycle, explicit foreground capture, native Echo Relay status/command handling, settings and optional fallbacks. No private IDs or dependencies on Hauszentrale; English/German settings and main state labels. Detailed backend error text may be German or supplied by HA.

## Routing fix / Weiterleitung ab HA-Integration 1.4.2

Bei den Jarvis-Pipelines „Befehle bevorzugt lokal verarbeiten“ (`prefer_local_intents`) ausschalten. Jarvis prüft zuerst Kamerafragen und Dialoge und übergibt gewöhnliche Hausbefehle weiterhin an den eingebauten HA-Assistenten, bevor freie Fragen an das Sprachmodell gehen. Sonst kann HA „Wer ist an der Haustür?“ als allgemeine Anwesenheitsfrage abfangen und nur „Keins“ antworten. Auch „Was siehst du an der Haustür?“ ist jetzt enthalten. Andere Assist-Pipelines behalten ihre bisherige Einstellung.

For Jarvis router pipelines disable “Prefer handling commands locally”. The router handles explicit camera questions first and still delegates ordinary device commands to native HA before using an LLM. Other pipelines need no change. Integration 1.4.2 adds an administrator-only `jarvis_tablet_audio.camera_pipeline_check` diagnostic accepting camera questions only; it runs the real configured intent pipeline without microphone capture, TTS or playback. Inspect `speech`, `processed_locally`, `prefer_local_intents` and `errors`. A camera answer should reach Jarvis (`processed_locally: false`). No Android update is required.

## Liveansicht und Vorderseite / Live view and front camera (1.4.3)

„Was siehst du in der Vorderkamera?“ und „Was siehst du an der Vorderseite?“ verwenden die konfigurierte Außenkamera. „Zeig mir die Außenkamera“ und „Was zeigt die Vorderkamera?“ sind ebenfalls enthalten. Die gemeinsame serverseitige Zuordnung gilt für Bildbeschreibung und Vorschau.

Karte 1.0.3 und Vorschaumodul 1.1.0 starten die HA-Liveansicht stumm, ohne zusätzlichen Startknopf. Nach der Sprachantwort schließt die Infobox entsprechend „Infobox-Anzeige“ in den Jarvis-Einstellungen (Standard 30 s); die eigenständige Karte verwendet `camera_info_seconds` (15–90, Standard 30). „Länger anzeigen (+60 s)“ verlängert einmalig, insgesamt höchstens drei Minuten ab Öffnung. Schließen, eine neue Frage, Tabwechsel oder Verlassen des Dashboards beendet die Anzeige und trennt den Player. Andere HA-Karten und Aufnahmen werden dadurch nicht gestoppt. Ohne verfügbare Kamera bleibt die Fehlermeldung sichtbar, bis die Infobox schließt. Der Tablet-Feed besteht weiterhin aus aktualisierten Einzelbildern.

The configured outdoor camera now answers “Vorderkamera” and “Vorderseite” visual questions. The live preview uses Home Assistant's standard picture-entity card in live mode with muted playback. It reuses the kiosk infobox delay (30 seconds by default after speech) or standalone `camera_info_seconds`, supports one 60-second extension and always closes within three minutes. Closing, a new question, hiding or removing the dashboard disposes the player. Description text still concerns a snapshot. Copy the new versioned JavaScript files and reload the dashboard; update the HA integration to 1.4.3 and restart HA for the new aliases. No APK or worker update is needed.
