# Archiv – ältere Jarvis-Kamera-Anleitung

**Aktuell:** [TAFA Kamera](../camera-preparation.de.md). Nicht für Neuinstallationen.

# Tablet-Kamera mit TAFA – TAFA Device Bridge 1.0.6 + HA-Integration 0.4.24

**Aktueller Weg für frische TAFA-Installationen:** Der Kamera-Empfänger ist bereits Bestandteil der einheitlichen TAFA-Integration. **Jarvis Tablet Audio muss nicht separat installiert werden.** Die folgenden älteren Jarvis-Anleitungen weiter unten gelten nur für historische Installationen.

1. Auf dem **gewählten Testserver** TAFA App **0.3.40** und die enthaltene HA-Integration **0.4.24** installieren und HA Core nach dem Backend-Update einmal neu starten.
2. Home Assistant → **Apps → TAFA → Benutzeroberfläche → Geräte & Multiroom → Tablet-Kameras je Raum** öffnen und die Kamera für deinen Raum (z. B. `buero`) ausdrücklich **An** schalten und speichern. Standardmäßig sind Kamera-Uploads **Aus**.
3. Auf dem Tablet **TAFA Device Bridge 1.0.6** mit dem Token des **Nicht-Admin-Raumnutzers** für diesen Testserver verwenden. Keine Administratorberechtigung nötig. Kamera in der App öffnen, Objektiv wählen, Berechtigung erteilen und **Kamera für HA starten** tippen. Der Audioplayer und die Rufworterkennung dürfen unabhängig davon laufen.
4. Home Assistant erzeugt die Kameras und Bewegungssensoren pro Raum unter der TAFA-Integration. Die Kameraübertragung läuft über authentifizierte `/api/tablet_assist_for_alexa/room_camera/register` und `/frame`, niemals über `/api/jarvis_echo_relay`.
5. Zum Beenden auf dem Tablet **HA-Kamera stoppen** drücken oder die Kamerafreigabe für den Raum in TAFA ausschalten. Bei letzterem wird auch das zuletzt gehaltene Bild verworfen.

Die Kamera sendet nur nach ausdrücklichem Start Einzelbilder, keine Aufzeichnung oder Offline-Warteschlange. Bilder werden im RAM gehalten und verfallen ohne neue Bilder. Wenn Betroffene erkennbar sind, deren Privatsphäre beachten. Verbindungsfehler: **404** bedeutet, dass der TAFA-Kamera-Endpunkt auf dem ausgewählten HA fehlt; **403** bedeutet Raum-/Benutzer-Berechtigung oder noch nicht aktivierte Kamerafreigabe; **409** bedeutet eine konkurrierende Tablet-Kamerasitzung.

---

## Historische Jarvis-Kamera-Dokumentation (nicht für neue TAFA-Installationen)

# Kamera und lokales Visionmodell · 0.5.0

[English](camera-preparation.md) | **Deutsch** · [Projektübersicht](../../README.de.md)

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

## Protokoll und Validierung

- Authentifiziertes `POST /api/jarvis_echo_relay/register` koppelt eine stabile Geräte-ID aus 32 Hex-Zeichen und liefert eine kurzlebige Sitzung.
- `POST /api/jarvis_echo_relay/frame` akzeptiert JPEGs bis 2 MiB mit Sitzung/Gerät, aufsteigender Sequenz, Aufnahmezeit und optionalen Bewegungs-Headern. Metadaten werden entfernt. Nur das neueste Bild bleibt erhalten; alte Sitzungen und Bilder werden abgewiesen.
- `DELETE /api/jarvis_echo_relay/frame` beendet die Sitzung und löscht das Bild.
- Native Android-Tests verwenden emulierte Kameras und einen privaten HTTP-Empfänger für Hintergrundübertragung, Authentifizierung, Sequenz/Bewegung und Remote-Stopp.
- `tests/relay_camera_e2e/run.sh` prüft Kopplung, Kamera-/Bewegungsentitäten, Autorisierung, Optionen/Neuladen, Sprachrouting sowie veraltete Bilder in einer isolierten HA-Installation mit synthetischen Bild-/Modell-Testdaten. Veröffentlichung setzt diese und die Android-Prüfungen voraus.

![Kameraansicht mit emulierter Szene](ui-camera-tablet.png)

## Weiterleitung ab HA-Integration 1.4.2

Bei den Jarvis-Pipelines „Befehle bevorzugt lokal verarbeiten“ (`prefer_local_intents`) ausschalten. Jarvis prüft zuerst Kamerafragen und Dialoge und übergibt gewöhnliche Hausbefehle weiterhin an den eingebauten HA-Assistenten, bevor freie Fragen an das Sprachmodell gehen. Sonst kann HA „Wer ist an der Haustür?“ als allgemeine Anwesenheitsfrage abfangen und nur „Keins“ antworten. Auch „Was siehst du an der Haustür?“ ist jetzt enthalten. Andere Assist-Pipelines behalten ihre bisherige Einstellung.

Die Administrator-Diagnose `jarvis_tablet_audio.camera_pipeline_check` akzeptiert nur Kamerafragen und prüft die konfigurierte Intent-Pipeline ohne Aufnahme, TTS oder Wiedergabe. `speech`, `processed_locally`, `prefer_local_intents` und `errors` prüfen; Kamerafragen sollen Jarvis erreichen (`processed_locally: false`). Kein Android-Update erforderlich.

## Liveansicht und Vorderseite (1.4.3)

„Was siehst du in der Vorderkamera?“ und „Was siehst du an der Vorderseite?“ verwenden die konfigurierte Außenkamera. „Zeig mir die Außenkamera“ und „Was zeigt die Vorderkamera?“ sind ebenfalls enthalten. Die gemeinsame serverseitige Zuordnung gilt für Bildbeschreibung und Vorschau.

Karte 1.0.3 und Vorschaumodul 1.1.0 starten die HA-Liveansicht stumm, ohne zusätzlichen Startknopf. Nach der Sprachantwort schließt die Infobox entsprechend „Infobox-Anzeige“ in den Jarvis-Einstellungen (Standard 30 s); die eigenständige Karte verwendet `camera_info_seconds` (15–90, Standard 30). „Länger anzeigen (+60 s)“ verlängert einmalig, insgesamt höchstens drei Minuten ab Öffnung. Schließen, eine neue Frage, Tabwechsel oder Verlassen des Dashboards beendet die Anzeige und trennt den Player. Andere HA-Karten und Aufnahmen werden dadurch nicht gestoppt. Ohne verfügbare Kamera bleibt die Fehlermeldung sichtbar, bis die Infobox schließt. Der Tablet-Feed besteht weiterhin aus aktualisierten Einzelbildern.

Versionierte JavaScript-Dateien kopieren, HA-Integration auf 1.4.3 aktualisieren, HA neu starten und Dashboard neu laden. Kein APK-/Worker-Update erforderlich.

## Nur anzeigen oder beschreiben (1.4.4)

Ab Karte 1.0.4 und Vorschaumodul 1.2.0 sind Anzeigen und Bildauswertung getrennt:

| Befehl | Verhalten |
|---|---|
| „Zeige Haustürkamera“, „Zeige Haustür Kamera“, „Haustür“, „Haustürkamera“, „Kamera Haustür“, „Klingel“ | Nur Haustür-Feed, ohne KI-Auswertung oder Sprachausgabe |
| „Zeige Vorderseite“, „Vorderseite“, „Vorderkamera“, „Vorderseite Kamera“, „Kamera Vorderseite“, „Zeig mir die Außenkamera“ | Nur Vorderseiten-/Außen-Feed |
| „Zeige Kameras“, „Zeig mir alle Kameras“ | Übersicht der eingerichteten, für den Benutzer freigegebenen Kameras; Tablet nur bei frischem Bild |
| „Was siehst du in der Haustürkamera?“, „Wer ist an der Haustür?“, „Was ist an der Klingel?“ | Haustür-Feed plus ausdrücklich angeforderte Bildbeschreibung |
| „Was siehst du an der Vorderseite?“, „Was zeigt die Vorderkamera?“, „Was ist draußen los?“ | Außen-Feed plus Bildbeschreibung |

Bei reiner Anzeige startet die Schließzeit sofort mit dem Öffnen. Bei einer Beschreibung beginnt sie nach der Sprachantwort. Verlängerung, maximale Öffnungsdauer und Beenden aller Player bleiben gleich. „Öffne die Haustür“ bleibt ein Hausbefehl und wird nicht zur Kameraanzeige. Definitionsfragen wie „Was ist eine Haustürkamera?“ werten kein Kamerabild aus.

Reine Anzeige umgeht Assist/TTS und Vision-Worker vollständig. Die Kameraübersicht zeigt bis zu drei autorisierte Feeds. Nativer Companion Assist kann diese lokale Ansicht nicht öffnen und gibt stattdessen einen Hinweis aus. Backend 1.4.4, Modul und Controller aktualisieren, HA neu starten und Dashboard neu laden. Kein APK-/GPU-Worker-Update nötig.

## KI-Modelle und Leistung (1.5.0)

In den Jarvis-Einstellungen **Assistent und Audio → KI-Modelle und Leistung** öffnen. Voraussetzung: GPU Worker 1.8.0 und HA-Administrator. Das Panel zeigt installierte Text-/Bildmodelle sowie aktuell geladene Modelle und deren Ollama-GPU-Speicher. Ein Modell wird nicht allein durch Öffnen des Panels geladen.

- Gemeinsam: Textmodell und Bildmodell auf **Qwen3-VL 4B Instruct** setzen.
- Getrennt: Textmodell **Qwen3 4B Instruct**, Bildmodell **Qwen3-VL 4B Instruct**.
- Warmhaltezeit: sofort entladen oder 1/2/5/10 Minuten. Sie gilt nach Speichern für beide Anfragearten.
- Kontext: 2048/4096/8192 Tokens, ebenfalls für beide gleich. Mehr Kontext benötigt mehr GPU-Speicher.
- **Für Jarvis speichern** übernimmt die Werte zentral für alle Geräte. Änderungen gelten für die nächste Anfrage; während Jarvis verarbeitet/spricht wird nicht gespeichert. Vorhandene Systemprompts, Werkzeuge, Gesprächsverlauf-Einstellungen und Kamera-Kopplung bleiben erhalten. **Status aktualisieren** lädt den tatsächlichen Zustand neu.

[jarvis-model-settings-v1.0.0.js](../../homeassistant/www/jarvis/jarvis-model-settings-v1.0.0.js) neben den Controller nach `/config/www/jarvis/` kopieren (kein separater Ressourceneintrag). Controller 1.0.5 lädt das Panel dynamisch. Backend 1.5.0 und Worker 1.8.0 verwenden; HA neu starten und Dashboard neu laden. Einstellungen werden serverseitig gespeichert. Nur installierte, erlaubte Modelle sind auswählbar. Kamera, STT und TTS bleiben unverändert. Keine automatischen Downloads. Ollama auf ein Modell begrenzen. Kein APK-Update nötig.

`jarvis_tablet_audio.model_settings` mit `action: get` liefert eine Revision; `action: set` erwartet Revision, `text_model`, `vision_model`, `keep_alive` und `num_ctx`. Nichtadministratoren sowie veraltete/ungültige Einstellungen werden abgewiesen. Worker-Schlüssel und Systemprompts werden nicht zurückgegeben.
