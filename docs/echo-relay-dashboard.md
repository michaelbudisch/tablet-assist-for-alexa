# Echo Relay Assist dashboard / Lovelace-Karte (v1.2.0)

## Bewegungsgesteuerte Aktionen / Motion-triggered actions

Voraussetzung: **Jarvis Tablet Audio 1.6.0**, **GPU Worker 1.9.0**, App **0.5.0** mit aktivierter Kamera und Bildbewegung. Die App selbst benötigt kein Update. Alle fünf Frontend-Dateien nach `/config/www/jarvis/` kopieren: `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js`, **`jarvis-proactive-v1.0.0.js`**. Nur die Assist-Karte als Ressource registrieren. Backend aktualisieren, HA einmal neu starten und Dashboard vollständig neu laden.

1. Unter **Jarvis → Proaktive Aktionen** als Administrator die Bewegungsauswertung einschalten. Sie ist bei einer neuen Installation aus.
2. Die [native Bewegungsautomation](../homeassistant/templates/echo-relay-proactive-automation.yaml) einmalig im HA-Automationseditor anlegen und die eigene Bewegungs-Entität auswählen. Der Dienst erzwingt alle Regeln; er läuft nicht als Dauerschleife.
3. **Testmodus** erlaubt wiederholte Prüfungen zu jeder Uhrzeit. Standard-Sperrzeit 60 Sekunden, wählbar 30 Sekunden bis 30 Minuten. Ohne Testmodus gilt das Morgen-Zeitfenster mit höchstens einer ausgeführten Aktion pro lokalem Kalendertag und mindestens fünf Minuten Sperrzeit. Gleiche Start-/Endzeit bedeutet ganztägig.
4. Unter **Begrüßung und Wetter** optional eine feste Anrede und eine Wetter-Entität wählen. Die Anrede gilt für jeden Treffer der ausgewählten Begrüßungskategorie; sie ist ausdrücklich keine Personenidentifikation. Leere Anrede ist der Standard. Regenhinweise werden nur aus einer passenden HA-Vorhersage übernommen; bei fehlenden Daten wird kein Regen behauptet.
5. **Erkennungen und HA-Automationen** bietet Person, grobe Einschätzung erwachsen/Kind und Hund. Unsichere Ergebnisse lösen nichts aus. Das ausgewählte optionale Skript bekommt `jarvis_detection` als Variable. Ohne Skript können eigene Automationen auf `jarvis_echo_relay_detection` reagieren. Das Modell wählt niemals Dienste, Skripte oder Parameter.
6. Die Echo-Relay-Begrüßung braucht ein sichtbares, freies Dashboard mit bereitem Android-Player und gewählter Echo-Relay-Ausgabe. Erkannte Sprache, Verarbeitung, Antworten und versteckte Dashboards werden übersprungen. Passives Warten auf das Rufwort oder mindestens zwei Sekunden Stille im Dauerbetrieb kann kurz pausiert werden; der eingestellte Hörmodus bleibt danach erhalten. HA vergibt genau einen Wiedergabeauftrag; mehrere Dashboards sprechen nicht gleichzeitig.
7. Mit „Tagesüberblick anbieten“ öffnet sich nach der Begrüßung ein kurzes Gesprächsfenster. „Ja bitte“ wird zur Frage „Was steht heute an?“; „Nein danke“ beendet die Rückfrage. Der Kiosk nutzt seine vorhandene Tagesübersicht; die eigenständige Karte gibt die Frage an ihre konfigurierte Assist-Pipeline weiter. Ein persönlicher Kalender wird dadurch nicht eingerichtet.

**Jetzt prüfen und Aktionen ausführen** verwendet das aktuelle Bild ohne erforderliches Bewegungssignal. Opt-in, Sperrzeit und alle Aktionsregeln bleiben aktiv; der Test kann tatsächlich sprechen oder das konfigurierte Skript starten. Der Status erklärt leere/unsichere Bilder, Sperrzeit, belegte Sprachverarbeitung und unerreichbare Worker. Nur nach vom Tablet bestätigtem Wiedergabestart zählt eine Begrüßung als tägliche Aktion. Es werden keine Bilder archiviert; nur Einstellungen und das Datum der letzten ausgeführten Tagesaktion bleiben gespeichert.

The feature is opt-in and requires backend 1.6.0, GPU Worker 1.9.0 and all five frontend modules. Install the native motion automation once. **Test mode repeats at any time**, subject to the configured cooldown; normal mode uses the morning window, a minimum five-minute cooldown and at most one action per local day. No computer wake-up, scheduled polling or continuous vision inference. The worker returns a fixed validated schema for people, dogs and coarse adult/child/unknown appearance; uncertain or invalid results trigger nothing. No identity, face comparison or gender inference.

Optional fixed greeting names are configuration and apply to every matching category. Rain advice comes from an actual HA forecast. A visible idle authenticated dashboard claims a single native Echo Relay stream, waits for playback confirmation and optionally listens for a yes/no follow-up. Ordinary questions take precedence over new proactive checks. A manually selected HA script receives `jarvis_detection`; other automations can listen for `jarvis_echo_relay_detection` with `labels`, `camera_entity_id`, `detection` and `test_mode`. No image is included in events. Script execution marks the daily guard; greetings mark it only after confirmed tablet playback. One shared cooldown limits checks; restart resets the in-memory cooldown but retains settings and the daily action date.

Administrative API: `jarvis_tablet_audio.proactive`, `action: get` returns a revision and status; `action: set` requires that revision and the complete `settings` dictionary. `action: check` is available to HA automations or administrators. `heartbeat`, `claim` and `ack` are used by authorized dashboard clients. Worker `/detect` accepts only bounded images and allowlisted model/residency/context values. Existing camera questions and view-only commands remain separate from this explicitly enabled automatic feature.

## Neue Einstellungen / Updated settings

Die Einstellungen verwenden in der öffentlichen Lovelace-Karte und im optionalen Kiosk dieselben Module. Fünf Reiter ersetzen die lange Liste:

| Bereich / Section | Einstellungen / Settings | Speicherung / Storage |
|---|---|---|
| Sprache & Audio / Voice & audio | Audioausgabe, Tablet-Reserve, Sprechpause, Empfindlichkeit, Anschlussfragen, Gesprächsfenster | Je Browser und Karteninstanz / Per browser and card instance |
| Anzeige & Kameras / Display & cameras | Untertitel, Anzeigedauer, Kamera-Infobox-Dauer und Einrichtungshinweise | Je Browser und Karteninstanz / Per browser and card instance |
| KI & Leistung / AI & performance | Textmodell, Bildmodell, Warmhaltezeit, Kontext, geladene Modelle | Zentral in HA, Administrator / Shared HA settings, administrator only |
| Proaktive Aktionen / Proactive actions | Opt-in, Testmodus, Sperrzeit, Begr??ung, Wetter und HA-Aktionen | Zentral in HA / Shared HA settings |
| Verlauf & Diagnose / History & diagnostics | Sitzungshistorie, Test, Wiederholung, Reserve, Browserwerte zurücksetzen | Verlauf nur im Arbeitsspeicher / History in memory only |

Modelle und zentrale Helfer werden mit sichtbaren Auswahlfeldern statt überlagerten Dropdown-Menüs gewählt. HA-Statusupdates ersetzen die Bedienelemente nicht. Bei zentralen Helfern bleibt eine Auswahl bis zur HA-Bestätigung erhalten; Fehler stehen direkt am Feld. Tabs lassen sich mit Pfeiltasten, Home und End bedienen. Farben folgen dem HA-Theme beziehungsweise den vorhandenen Kiosk-Farben.

Model and helper choices use inline radio controls instead of dropdown overlays. Live state updates preserve control nodes and pending selections; failed helper saves restore the confirmed value and display a local error. Tabs support arrow keys, Home and End. Colours follow the active HA theme. Browser changes are immediate; shared model changes require **Save for Jarvis**. Resetting browser defaults never changes shared models.

Das [vollständige Lovelace-Beispiel](../homeassistant/templates/echo-relay-dashboard.yaml) benötigt keine private Hauszentrale. Optional **jarvis-control-panel-v1.6.0.js** zusätzlich als Ressource registrieren und `custom:jarvis-control-panel` ergänzen. Dieses zweite Panel setzt die konfigurierten Helfer und Skripte der manuellen Altinstallation voraus und gruppiert Stimme/System, Durchsagen, Hinweise/Räume und Timer/Tablet. Der Installer liefert beide Karten und alle abhängigen Module mit. Nur eine Version jedes Controllers als Ressource laden; den bisherigen Ressourceneintrag ersetzen und danach das Dashboard vollständig neu laden.

The [portable Lovelace example](../homeassistant/templates/echo-relay-dashboard.yaml) works without the private kiosk. The optional `jarvis-control-panel` 1.6.0 also needs the legacy package helpers/scripts and configured room entities. It groups voices/system, announcements, notifications/rooms and timers/tablet. Copy the complete staged output when installing from scratch. Replace the old controller resource entry; loading two versions of one custom element does not upgrade an already registered element. Update to Jarvis Tablet Audio 1.6.0 and GPU Worker 1.9.0, restart HA once, then reload the dashboard.

Die gemeinsame Oberfläche zeigt zusätzliche Kiosk-Steuerungen nur dort, wo deren Funktionen vorhanden sind: Hausdatenkarten, Kontext-Navigation, Rückkehr zur Hausansicht und Wikipedia-Aufbereitung gehören zur privaten Hauszentrale. Die eigenständige Karte bietet ihre funktionsfähigen Audio-, Gesprächs-, Untertitel-, Verlauf-, Kamera- und KI-Einstellungen direkt an; es gibt keine wirkungslosen Platzhalter für private Hausansichten. Die Android-App und deren Kamera-Freigabe werden weiter in der App eingerichtet. Die separate Marketplace-Seitenleiste ist keine Lovelace-Karte und wird durch diesen Ressourcentausch nicht ersetzt.

Additional kiosk-only controls appear when the host supports their features: home-data cards, navigation/return to private home views and Wikipedia presentation. The standalone card exposes its working audio, conversation, captions, history, camera and AI preferences. Android camera sharing remains configured in the app. The separate Marketplace sidebar is not replaced by this Lovelace resource update.

**Nachfragen:** Automatisch nutzt das Gesprächsfenster; „Bei Rückfragen“ öffnet das Mikrofon nach einer Frage in der Antwort oder einer Assist-Nachfrage. „Nur auf Assist-Anfrage“ folgt ausschließlich `continue_conversation`. Im Kiosk berücksichtigt der intelligente Modus zusätzlich dessen Wissenskontext. Sprechpause und Empfindlichkeit gelten ab der nächsten Aufnahme; Kamera-Schließzeiten ab der nächsten Infobox.

Independent of the private Hauszentrale dashboard. Works with a Home Assistant dashboard and the Android Echo Relay command/status helper protocol. No changes to the APK. Browser tests cover German/English settings, theme/layout changes, delayed HA acknowledgements, model saves and the camera lifecycle. Physical microphones, Echo devices and Android WebViews still require testing on your own hardware.

## Deutsch

1. Echo Relay installieren, mit HA verbinden und den Echo als Bluetooth-Medienausgang auswählen. Player starten. Das Mikrofon wird vom sichtbaren HA-Dashboard verwendet, nicht von der Relay-App.
2. Unter **Einstellungen → Geräte & Dienste → Helfer** zwei Text-Helfer mit maximal 255 Zeichen anlegen: `input_text.jarvis_native_audio_command` und `input_text.jarvis_native_audio_status`. Vorhandene Helfer wiederverwenden. Alternativ die [YAML-Vorlage](../homeassistant/templates/echo-relay-helpers.yaml) in die bestehende, korrekt konfigurierte packages-Struktur übernehmen; keine doppelten Definitionen.
3. Die fünf Dateien `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js` und `jarvis-proactive-v1.0.0.js` aus [homeassistant/www/jarvis](../homeassistant/www/jarvis/) nach `/config/www/jarvis/` kopieren. Nur `/local/jarvis/echo-relay-assist-card-v1.2.0.js?v=1.2.0` unter Einstellungen → Dashboards → Ressourcen als JavaScript-Modul registrieren.
4. Eine manuelle Karte in einem beliebigen Dashboard hinzufügen (Beispiel unten). Die bevorzugte Assist-Pipeline wird ohne Angabe verwendet. Wenn nötig eigene `pipeline_id` (STT/Intent/TTS) und `wake_pipeline_id` (Wakeword/STT) eintragen. Für Rufwortmodus ist ein konfigurierter serverseitiger Wakeword-Dienst erforderlich; ohne ihn Dauerbetrieb/Einmal sprechen verwenden.
5. Mikrofonberechtigung im HTTPS-Dashboard erteilen. Einmal drücken = Rufwort (grün), zweimal = Dauerbetrieb (blau), dreimal = aus. Beim Wechsel auf einen nicht sichtbaren Tab oder beim Entfernen der Karte stoppt sie. Nach Reload startet die Aufnahme manuell; eine ausdrücklich aktivierte proaktive Rückfrage kann nach einer Begrüßung ebenfalls kurz das Mikrofon öffnen. Während der Antwort ist das Mikrofon geschlossen. Nach Sprechpausen oder Antworten hört der Dauerbetrieb erneut zu.
6. Im aufklappbaren Einstellungsbereich Echo Relay (Standard), Tablet/Bluetooth oder nativen Assist als Reserve wählen. Der Hauptbutton steuert immer den integrierten Assistenten. Der Android-Assistent wird als explizite Reserve geöffnet. Bei paralleler nativer Wakeword-Erkennung diese in der Companion App abschalten; optional `native_notify_service` mit passendem `mobile_app_...`-Dienst konfigurieren.
7. Nur eine aktive Karte/Bedienstelle pro Echo Relay Helper-Paar. Informiere Anwesende über die aktive Mikrofonaufnahme. Die App bestätigt die Audioausgabe; wie schnell das Streaming startet, hängt von der App-Version ab. Ab App-Version 0.3.0 werden MP3 und PCM/WAV fortlaufend mit kleinem Anfangspuffer abgespielt; Version 0.2.0 lädt noch die vollständige Datei.

## English

1. Install Echo Relay on Android, pair the Echo using system Bluetooth settings, connect the app to HA and start its player.
2. Create two Text helpers (maximum 255 characters): `input_text.jarvis_native_audio_command` and `input_text.jarvis_native_audio_status`. Reuse existing helpers, or use the optional [YAML template](../homeassistant/templates/echo-relay-helpers.yaml) in a configured packages directory. Do not define them twice.
3. Copy the five files `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js` and `jarvis-proactive-v1.0.0.js` from [homeassistant/www/jarvis](../homeassistant/www/jarvis/) into `/config/www/jarvis/`. Register only `/local/jarvis/echo-relay-assist-card-v1.2.0.js?v=1.2.0` as a Dashboard Resource of type JavaScript module.
4. Use your preferred HA Assist pipeline, or set your own pipeline IDs below. Wake-word mode needs a configured server-side wake-word engine. Continuous and one-shot modes do not require it. Use HTTPS and grant microphone access.
5. Tap the microphone: green wake word → blue continuous → off. It stops when hidden or disconnected. Recording starts manually after a reload; an explicitly enabled proactive follow-up may also briefly open the microphone after a greeting. Capture pauses during playback and reopens for the next turn in continuous mode. Inform people nearby.
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

Mit **Jarvis Tablet Audio 1.5.0** und **GPU Worker 1.8.0**: Außen-/Haustürkamera in den Integrationsoptionen auswählen. Fragen wie „Wer ist an der Haustür?“, „Was ist an der Haustür?“ und „Was ist draußen los?“ öffnen die zugeordnete Kamera in einer Jarvis-Kamera-Infobox im anfragenden, sichtbaren Dashboard. Gleichzeitig beschreibt Jarvis das abgerufene Einzelbild. Personen werden nur anhand sichtbarer Merkmale wie Kleidung oder mitgeführter Gegenstände beschrieben; keine Namenszuordnung oder Gesichtserkennung. Die Infobox startet die Liveansicht stumm, während die Beschreibung ein Einzelbild betrifft. Alle Bildbeschreibungen können falsch sein.

With Jarvis Tablet Audio 1.5.0 and GPU Worker 1.8.0, configured door/outdoor/tablet camera questions open the corresponding Jarvis camera infobox only on the requesting visible dashboard. Jarvis describes a snapshot, including generic visible people, clothing and carried objects, without identity recognition. The dialog automatically starts a muted live view; the description remains a single-image observation and may be wrong. Other devices, hidden dashboards and native Companion Assist do not automatically open this dialog. Ordinary door controls retain their existing route. A failed preview never interrupts the spoken response.

App **0.5.0** continues to work; no APK update is required. Copy all five JavaScript files, update the card resource, restart HA after the backend update, then reload the dashboard. This also applies to the separately maintained Hauszentrale Kiosk controller when its preview hook is installed.

## Changes / Änderungen

- v1.1.0: shared theme-aware settings with four keyboard-accessible tabs; inline model and central helper choices; portable microphone, conversation, caption, history and fallback preferences. Optional control panel 1.6.0 groups house functions and preserves choices while HA acknowledges changes.

- v1.0.5: administrator model selection, shared residency/context and loaded-model status.

- v1.0.4: silent view-only camera commands and an authorized camera overview; explicit visual questions retain snapshot descriptions.

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

## Nur anzeigen oder beschreiben / View or describe (1.4.4)

Ab Karte 1.0.4 und Vorschaumodul 1.2.0 sind Anzeigen und Bildauswertung getrennt:

| Befehl | Verhalten |
|---|---|
| „Zeige Haustürkamera“, „Zeige Haustür Kamera“, „Haustür“, „Haustürkamera“, „Kamera Haustür“, „Klingel“ | Nur Haustür-Feed, ohne KI-Auswertung oder Sprachausgabe |
| „Zeige Vorderseite“, „Vorderseite“, „Vorderkamera“, „Vorderseite Kamera“, „Kamera Vorderseite“, „Zeig mir die Außenkamera“ | Nur Vorderseiten-/Außen-Feed |
| „Zeige Kameras“, „Zeig mir alle Kameras“ | Übersicht der eingerichteten, für den Benutzer freigegebenen Kameras; Tablet nur bei frischem Bild |
| „Was siehst du in der Haustürkamera?“, „Wer ist an der Haustür?“, „Was ist an der Klingel?“ | Haustür-Feed plus ausdrücklich angeforderte Bildbeschreibung |
| „Was siehst du an der Vorderseite?“, „Was zeigt die Vorderkamera?“, „Was ist draußen los?“ | Außen-Feed plus Bildbeschreibung |

Bei reiner Anzeige startet die Schließzeit sofort mit dem Öffnen. Bei einer Beschreibung beginnt sie nach der Sprachantwort. Verlängerung, maximale Öffnungsdauer und Beenden aller Player bleiben gleich. „Öffne die Haustür“ bleibt ein Hausbefehl und wird nicht zur Kameraanzeige. Definitionsfragen wie „Was ist eine Haustürkamera?“ werten kein Kamerabild aus.

View-only commands bypass the dashboard Assist/TTS pipeline entirely and never call the vision worker. Bare camera aliases also show the feed. Explicit visual questions (or an explicit “describe” request) still infer a snapshot and speak its description. “Zeige Kameras” opens up to three authorized configured feeds in one responsive grid; closing the infobox removes every player. Native Companion Assist cannot open this dashboard-local view and returns a short dashboard hint, without inference. Update backend 1.4.4, the versioned module and controller, then restart HA and reload the dashboard. No APK or GPU-worker update is required.

## KI-Modelle und Leistung / AI models and performance (1.5.0)

In den Jarvis-Einstellungen **KI & Leistung → KI-Modelle und Leistung** öffnen. Voraussetzung: GPU Worker 1.8.0 und HA-Administrator. Das Panel zeigt installierte Text-/Bildmodelle sowie aktuell geladene Modelle und deren Ollama-GPU-Speicher. Ein Modell wird nicht allein durch Öffnen des Panels geladen.

- Gemeinsam: Textmodell und Bildmodell auf **Qwen3-VL 4B Instruct** setzen.
- Getrennt: Textmodell **Qwen3 4B Instruct**, Bildmodell **Qwen3-VL 4B Instruct**.
- Warmhaltezeit: sofort entladen oder 1/2/5/10 Minuten. Sie gilt nach Speichern für beide Anfragearten.
- Kontext: 2048/4096/8192 Tokens, ebenfalls für beide gleich. Mehr Kontext benötigt mehr GPU-Speicher.
- **Für Jarvis speichern** übernimmt die Werte zentral für alle Geräte. Änderungen gelten für die nächste Anfrage; während Jarvis verarbeitet/spricht wird nicht gespeichert. Vorhandene Systemprompts, Werkzeuge, Gesprächsverlauf-Einstellungen und Kamera-Kopplung bleiben erhalten. **Status aktualisieren** lädt den tatsächlichen Zustand neu.

Copy [jarvis-model-settings-v1.1.0.js](../homeassistant/www/jarvis/jarvis-model-settings-v1.1.0.js) alongside the controller into `/config/www/jarvis/` (no separate resource entry). Controller 1.1.0 dynamically mounts the shared settings. Also copy jarvis-settings-v1.1.0.js into the same directory. Use backend 1.5.0 and worker 1.8.0, restart HA once after installing backend code and reload the dashboard. Settings are server-backed, not browser-local. Model changes do not restart the tablet camera. Only installed allowlisted models are offered; no automatic downloads. Shared text/vision uses the same model tag, context and residency; keep Ollama's existing one-model limit. Speech recognition and synthesis still use their existing services. No APK update is required.

For automation-free administration, `jarvis_tablet_audio.model_settings` with `action: get` returns a revision. `action: set` takes that revision plus `text_model`, `vision_model`, `keep_alive` and `num_ctx`. Non-admin requests and stale or unsupported settings are rejected. The service never returns worker credentials or system prompts.
