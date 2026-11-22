# Kamera und lokales Visionmodell · 0.5.0

## Einrichtung

1. HA benötigt den Kamera-Empfänger **Jarvis Tablet Audio 1.5.0** aus `homeassistant/custom_components/`. Bei bestehenden Installationen `const.py`, Zugangsdaten und eigene Dialog-/Sucherweiterungen behalten; Setup/Router gezielt um die Kameramodule ergänzen. Python-Codeupdates benötigen einen HA-Neustart. Neue portable Installationen verwenden `homeassistant/install.py`.
2. In **Einstellungen → Geräte & Dienste → Jarvis Tablet Audio → Konfigurieren** Außen-/Haustürkamera auswählen. Eine leere Vision-Adresse nutzt den vorhandenen GPU-Host auf Port 10503. Alternativ lokale IP mit Port ohne Pfad angeben. Der bestehende Qwen-/Worker-Schlüssel wird genutzt. Voraussetzung: GPU Worker 1.8.0 mit Vision-Profil und installiertem Visionmodell. Die App benötigt keinen weiteren produktiven Docker-Dienst.
3. In der App HA-Adresse/Token speichern, **Kameraeinstellungen öffnen**, Front-/Rückkamera auswählen, optional **Bildbewegung an HA melden** einschalten und **Kamera für HA starten** antippen. Die Kopplung benötigt einen HA-Administrator-Token. Der Audioplayer muss nicht laufen.
4. Bilder erscheinen normalerweise als `camera.echo_relay_tablet`, Bewegung als `binary_sensor.echo_relay_bildbewegung`. Bei abweichenden Namen die Entitäten der Integration verwenden. Der Vision-Aufruf findet die Tablet-Kamera anhand ihrer eindeutigen ID.
5. Mit dem Jarvis-Gesprächsrouter fragen: **„Was ist draußen los?“**, **„Wer ist an der Haustür?“**, **„Was ist an der Haustür?“**, **„Was sieht die Haustürkamera?“**, **„Was siehst du?“**, **„Was halte ich in der Hand?“**. Alternativ `jarvis_tablet_audio.describe_camera` mit `source: outside`, `door` oder `tablet` und `mode: scene`, `objects` oder `object_in_hand` aufrufen. Die Aktion gibt `description` zurück. Andere Gespräche und Hausbefehle behalten ihren bisherigen Weg.

## Kamera-Infobox und Haustürfragen

Der aktualisierte Dashboard-Controller öffnet bei einer Kamerafrage automatisch die zugeordnete Kamera als HA-Infobox, während Jarvis das Einzelbild beschreibt. Das gilt nur für das anfragende, sichtbare Dashboard, nicht für andere Tablets oder nativen Companion Assist. Für die öffentliche Karte Version 1.0.4 zusammen mit `jarvis-camera-preview-v1.2.0.js` installieren; nach dem Update Dashboard neu laden. App 0.5.0 benötigt dafür kein Update.

Bei „Wer ist an der Haustür?“ sind allgemeine Beschreibungen sichtbarer Personen, Kleidung und mitgeführter Gegenstände möglich. Das Modell ordnet keine Namen zu und führt keinen Gesichtsabgleich durch. Auch „Wer steht gerade vor der Tür?“ ist eine Kamerafrage. „Öffne die Haustür“ und „Ist die Haustür abgeschlossen?“ bleiben Hausbefehle beziehungsweise Statusfragen.

## Betrieb und Grenzen

Der separat gestartete Kamera-Vordergrunddienst bleibt nach Verlassen der App aktiv und hat eine eigene Stopp-Benachrichtigung. **HA-Kamera stoppen** beendet nur die Kamera. Audio und Keepalive bleiben unabhängig. Nach einem Neustart startet die Kamera nicht automatisch. Der lokale Kameratest ist separat und schließt seine Vorschau beim Verlassen.

Dies sind aktualisierte Einzelbilder ungefähr alle zwei Sekunden, kein Video mit voller Bildrate. Bilder bleiben im Arbeitsspeicher; es gibt keine Aufnahme, Offline-Warteschlange oder offenen Kamera-Port auf dem Tablet. Die Übertragung nutzt die gespeicherte HA-Adresse, Standard-TLS-Prüfung und HA-Authentifizierung ohne Weiterleitungen. Bei freigegebenem lokalem HTTP sind auch Bilder unverschlüsselt.

Die Kopplung bindet eine Tablet-ID an den HA-Administrator. Zum Wechsel das alte Tablet stoppen, dann als Administrator `jarvis_tablet_audio.unpair_camera` aufrufen. Stopp sperrt die Sitzung und löscht das Bild. Ohne Nachschub wird es nach 15 Sekunden nicht mehr als verfügbar angeboten. `jarvis_tablet_audio.camera_vision_status` prüft Worker und Kamera-Zuordnung ohne Bildübertragung.

Bildbewegung vergleicht grobe Pixeländerungen und unterdrückt gleichmäßige Helligkeitswechsel. Sie erkennt keine Personen/Objekte, kann Bewegungen übersehen und auf Licht reagieren. Für zuverlässige Video-/Objekterkennung eignet sich separat beispielsweise Frigate. Vision beschreibt ein Einzelbild und kann irren; Außenkameras können ein älteres Standbild liefern. Modellwechsel und Bildabruf können die Antwort verzögern. Dauerbetrieb und Display-aus-Verhalten hängen von Android und Akkuverwaltung ab.

## English

Use the matching HA receiver and existing GPU Worker vision service. Explicitly start camera delivery in app settings. Its dedicated foreground notification stops it independently of audio. Images are pushed roughly every two seconds using the saved HA origin and administrator token. No tablet image server, disk recording, automatic boot start or offline queue is created. Stop invalidates the session; images expire after 15 seconds without delivery. Select outdoor/door cameras in the integration options. `describe_camera` returns a description for tablet/outdoor/door images on explicit request.

Camera questions such as “Who is at the front door?” also open the configured camera in the requesting visible dashboard with card 1.0.3 and the shared preview module. Other dashboards and native Companion Assist do not open automatically. Visible people can be described generically without names or face matching. The existing 0.5.0 APK remains compatible; reload the updated dashboard.

## Protocol and validation

- Authenticated `POST /api/jarvis_echo_relay/register` pairs a stable 32-hex device ID and returns an ephemeral session.
- `POST /api/jarvis_echo_relay/frame` accepts JPEGs up to 2 MiB with session/device, increasing sequence, capture time and optional motion headers. Normalization strips metadata; only the latest image is retained. Old sessions/frames are rejected.
- `DELETE /api/jarvis_echo_relay/frame` stops the remote session and clears the image.
- Native Android tests use emulated cameras and a private HTTP receiver to verify background JPEG delivery, authentication, sequence/motion metadata and remote Stop.
- `tests/relay_camera_e2e/run.sh` tests pairing, camera/motion entities, authorization, options/reload, spoken routing and stale/late frames in isolated real HA with synthetic image/model fixtures. Publication waits for this check and Android checks.

![Camera screen with emulated scene](ui-camera-tablet.png)

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

In den Jarvis-Einstellungen **Assistent und Audio → KI-Modelle und Leistung** öffnen. Voraussetzung: GPU Worker 1.8.0 und HA-Administrator. Das Panel zeigt installierte Text-/Bildmodelle sowie aktuell geladene Modelle und deren Ollama-GPU-Speicher. Ein Modell wird nicht allein durch Öffnen des Panels geladen.

- Gemeinsam: Textmodell und Bildmodell auf **Qwen3-VL 4B Instruct** setzen.
- Getrennt: Textmodell **Qwen3 4B Instruct**, Bildmodell **Qwen3-VL 4B Instruct**.
- Warmhaltezeit: sofort entladen oder 1/2/5/10 Minuten. Sie gilt nach Speichern für beide Anfragearten.
- Kontext: 2048/4096/8192 Tokens, ebenfalls für beide gleich. Mehr Kontext benötigt mehr GPU-Speicher.
- **Für Jarvis speichern** übernimmt die Werte zentral für alle Geräte. Änderungen gelten für die nächste Anfrage; während Jarvis verarbeitet/spricht wird nicht gespeichert. Vorhandene Systemprompts, Werkzeuge, Gesprächsverlauf-Einstellungen und Kamera-Kopplung bleiben erhalten. **Status aktualisieren** lädt den tatsächlichen Zustand neu.

Copy [jarvis-model-settings-v1.0.0.js](../../homeassistant/www/jarvis/jarvis-model-settings-v1.0.0.js) alongside the controller into `/config/www/jarvis/` (no separate resource entry). Controller 1.0.5 dynamically mounts the panel. Use backend 1.5.0 and worker 1.8.0, restart HA once after installing backend code and reload the dashboard. Settings are server-backed, not browser-local. Model changes do not restart the tablet camera. Only installed allowlisted models are offered; no automatic downloads. Shared text/vision uses the same model tag, context and residency; keep Ollama's existing one-model limit. Speech recognition and synthesis still use their existing services. No APK update is required.

For automation-free administration, `jarvis_tablet_audio.model_settings` with `action: get` returns a revision. `action: set` takes that revision plus `text_model`, `vision_model`, `keep_alive` and `num_ctx`. Non-admin requests and stale or unsupported settings are rejected. The service never returns worker credentials or system prompts.
