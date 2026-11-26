# Archiv – Echo Relay Lovelace-Karten

**Aktuell:** [TAFA Multiroom](../../homeassistant/examples/MULTIROOM.de.md). Diese alten Schritte nicht für Neuinstallationen nutzen.

# Echo Relay Assist – Lovelace-Karte (v1.2.0)

> **Multiroom ab Android 0.6.0 / HA 1.7.0:** [Neue Raum-Einrichtung](../homeassistant/examples/MULTIROOM.de.md). Die folgende Anleitung gilt für den bisherigen Einzelgeräte-Modus mit globalen Helfern.

[English](en/echo-relay-dashboard.md) | **Deutsch** · [Projektübersicht](../README.de.md)

> **Aktueller optionaler Vorschaupfad:** [Native HA-Automationen und Familienfelder](ha-automations.md). Diese Seite beschreibt die ursprüngliche Karte 1.2.0 und ihre Einstellungen. Die optionale Karte 1.3.0 verwendet stattdessen Familienhelfer und die universelle Sprechaktion.

## Einrichtung

1. Echo Relay installieren, mit HA verbinden und den Echo als Bluetooth-Medienausgang auswählen. Player starten. Das Mikrofon wird vom sichtbaren HA-Dashboard verwendet, nicht von der Relay-App.
2. Unter **Einstellungen → Geräte & Dienste → Helfer** zwei Text-Helfer mit maximal 255 Zeichen anlegen: `input_text.jarvis_native_audio_command` und `input_text.jarvis_native_audio_status`. Vorhandene Helfer wiederverwenden. Alternativ die [YAML-Vorlage](../homeassistant/templates/echo-relay-helpers.yaml) in die bestehende, korrekt konfigurierte packages-Struktur übernehmen; keine doppelten Definitionen.
3. Die fünf Dateien `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js` und `jarvis-proactive-v1.0.0.js` aus [homeassistant/www/jarvis](../homeassistant/www/jarvis/) nach `/config/www/jarvis/` kopieren. Nur `/local/jarvis/echo-relay-assist-card-v1.2.0.js?v=1.2.0` unter Einstellungen → Dashboards → Ressourcen als JavaScript-Modul registrieren.
4. Eine manuelle Karte in einem beliebigen Dashboard hinzufügen (Beispiel unten). Die bevorzugte Assist-Pipeline wird ohne Angabe verwendet. Wenn nötig eigene `pipeline_id` (STT/Intent/TTS) und `wake_pipeline_id` (Wakeword/STT) eintragen. Für Rufwortmodus ist ein konfigurierter serverseitiger Wakeword-Dienst erforderlich; ohne ihn Dauerbetrieb/Einmal sprechen verwenden.
5. Mikrofonberechtigung im HTTPS-Dashboard erteilen. Einmal drücken = Rufwort (grün), zweimal = Dauerbetrieb (blau), dreimal = aus. Beim Wechsel auf einen nicht sichtbaren Tab oder beim Entfernen der Karte stoppt sie. Nach Reload startet die Aufnahme manuell; eine ausdrücklich aktivierte proaktive Rückfrage kann nach einer Begrüßung ebenfalls kurz das Mikrofon öffnen. Während der Antwort ist das Mikrofon geschlossen. Nach Sprechpausen oder Antworten hört der Dauerbetrieb erneut zu.
6. Im aufklappbaren Einstellungsbereich Echo Relay (Standard), Tablet/Bluetooth oder nativen Assist als Reserve wählen. Der Hauptbutton steuert immer den integrierten Assistenten. Der Android-Assistent wird als explizite Reserve geöffnet. Bei paralleler nativer Wakeword-Erkennung diese in der Companion App abschalten; optional `native_notify_service` mit passendem `mobile_app_...`-Dienst konfigurieren.
7. Nur eine aktive Karte/Bedienstelle pro Echo Relay Helper-Paar. Informiere Anwesende über die aktive Mikrofonaufnahme. Die App bestätigt die Audioausgabe; wie schnell das Streaming startet, hängt von der App-Version ab. Ab App-Version 0.3.0 werden MP3 und PCM/WAV fortlaufend mit kleinem Anfangspuffer abgespielt; Version 0.2.0 lädt noch die vollständige Datei.

```yaml
type: custom:echo-relay-assist-card
title: Echo Relay
# Optional:
# pipeline_id: YOUR_ASSIST_PIPELINE_ID
# wake_pipeline_id: YOUR_WAKEWORD_PIPELINE_ID
# native_notify_service: mobile_app_your_tablet
# status_entity: input_text.your_optional_debug_status
# output: native_audio
```

Befehls- und Statusentitäten verwenden standardmäßig die festen App-Helfer. `command_entity` und `relay_status_entity` nur ändern, wenn der Android-Client dasselbe Paar unterstützt. Optionale direkte Alexa-Reserve: `alexa_script: your_script_service_name` (ohne script-Präfix) und `alexa_notify: notify.your_echo`. Das Skript erwartet die Felder `text` und `lautsprecher`. Direkte Alexa-Durchsagen können Audio über die Amazon-Cloud übertragen; keine vertraulichen Antworten dafür verwenden. Die Browserkarte verwendet die authentifizierte HA-Verbindung und speichert keine HA-Token.

<a id="bewegungsgesteuerte-aktionen--motion-triggered-actions"></a>

## Bewegungsgesteuerte Aktionen

Voraussetzung: **Jarvis Tablet Audio 1.6.0**, **GPU Worker 1.9.0**, App **0.5.0** mit aktivierter Kamera und Bildbewegung. Die App selbst benötigt kein Update. Alle fünf Frontend-Dateien nach `/config/www/jarvis/` kopieren: `echo-relay-assist-card-v1.2.0.js`, `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js`, `jarvis-camera-preview-v1.2.0.js`, **`jarvis-proactive-v1.0.0.js`**. Nur die Assist-Karte als Ressource registrieren. Backend aktualisieren, HA einmal neu starten und Dashboard vollständig neu laden.

1. Unter **Jarvis → Proaktive Aktionen** als Administrator die Bewegungsauswertung einschalten. Sie ist bei einer neuen Installation aus.
2. Die [native Bewegungsautomation](../homeassistant/templates/echo-relay-proactive-automation.yaml) einmalig im HA-Automationseditor anlegen und die eigene Bewegungs-Entität auswählen. Der Dienst erzwingt alle Regeln; er läuft nicht als Dauerschleife.
3. **Testmodus** erlaubt wiederholte Prüfungen zu jeder Uhrzeit. Standard-Sperrzeit 60 Sekunden, wählbar 30 Sekunden bis 30 Minuten. Ohne Testmodus gilt das Morgen-Zeitfenster mit höchstens einer ausgeführten Aktion pro lokalem Kalendertag und mindestens fünf Minuten Sperrzeit. Gleiche Start-/Endzeit bedeutet ganztägig.
4. Unter **Begrüßung und Wetter** optional eine feste Anrede und eine Wetter-Entität wählen. Die Anrede gilt für jeden Treffer der ausgewählten Begrüßungskategorie; sie ist ausdrücklich keine Personenidentifikation. Leere Anrede ist der Standard. Regenhinweise werden nur aus einer passenden HA-Vorhersage übernommen; bei fehlenden Daten wird kein Regen behauptet.
5. **Erkennungen und HA-Automationen** bietet Person, grobe Einschätzung erwachsen/Kind und Hund. Unsichere Ergebnisse lösen nichts aus. Das ausgewählte optionale Skript bekommt `jarvis_detection` als Variable. Ohne Skript können eigene Automationen auf `jarvis_echo_relay_detection` reagieren. Das Modell wählt niemals Dienste, Skripte oder Parameter.
6. Die Echo-Relay-Begrüßung braucht ein sichtbares, freies Dashboard mit bereitem Android-Player und gewählter Echo-Relay-Ausgabe. Erkannte Sprache, Verarbeitung, Antworten und versteckte Dashboards werden übersprungen. Passives Warten auf das Rufwort oder mindestens zwei Sekunden Stille im Dauerbetrieb kann kurz pausiert werden; der eingestellte Hörmodus bleibt danach erhalten. HA vergibt genau einen Wiedergabeauftrag; mehrere Dashboards sprechen nicht gleichzeitig.
7. Mit „Tagesüberblick anbieten“ öffnet sich nach der Begrüßung ein kurzes Gesprächsfenster. „Ja bitte“ wird zur Frage „Was steht heute an?“; „Nein danke“ beendet die Rückfrage. Der Kiosk nutzt seine vorhandene Tagesübersicht; die eigenständige Karte gibt die Frage an ihre konfigurierte Assist-Pipeline weiter. Ein persönlicher Kalender wird dadurch nicht eingerichtet.

**Jetzt prüfen und Aktionen ausführen** verwendet das aktuelle Bild ohne erforderliches Bewegungssignal. Opt-in, Sperrzeit und alle Aktionsregeln bleiben aktiv; der Test kann tatsächlich sprechen oder das konfigurierte Skript starten. Der Status erklärt leere/unsichere Bilder, Sperrzeit, belegte Sprachverarbeitung und unerreichbare Worker. Nur nach vom Tablet bestätigtem Wiedergabestart zählt eine Begrüßung als tägliche Aktion. Es werden keine Bilder archiviert; nur Einstellungen und das Datum der letzten ausgeführten Tagesaktion bleiben gespeichert.

Keine geplante Dauerabfrage und kein automatisches Starten des KI-Rechners. Der Worker liefert ein validiertes Schema mit Personen-/Hundanzahl, grober Altersgruppe und beim aktualisierten Worker optionalen Erscheinungskategorien. Es handelt sich um Schätzungen, nicht um tatsächliche Geschlechts- oder Identitätsfeststellung. Das Ereignis enthält keine Bilder. Skriptausführung markiert die Tagesgrenze, Begrüßungen erst bei bestätigtem Wiedergabestart. Ein Neustart setzt die Sperrzeit im Arbeitsspeicher zurück, nicht Einstellungen oder Tagesdatum.

Administrator-API: `jarvis_tablet_audio.proactive` mit `action: get` liefert Revision und Status; `action: set` setzt die Revision und das vollständige Objekt `settings` voraus. `action: check` ist für HA-Automationen und Administratoren verfügbar. `heartbeat`, `claim` und `ack` dienen autorisierten Dashboards. `/detect` akzeptiert nur begrenzte Bilder und erlaubte Modell-, Kontext- und Warmhaltewerte.

## Einstellungen

Die öffentliche Karte und der optionale Kiosk verwenden gemeinsame Module.

| Bereich | Einstellungen | Speicherung |
|---|---|---|
| Sprache & Audio | Ausgabe, Reserve, Sprechpause, Empfindlichkeit, Rückfragen, Gesprächsfenster | Je Browser und Karteninstanz |
| Anzeige & Kameras | Untertitel, Anzeigedauer, Infobox-Dauer | Je Browser und Karteninstanz |
| KI & Leistung | Text-/Bildmodell, Kontext, Warmhaltezeit, geladene Modelle | Zentral in HA, Administrator |
| Proaktive Aktionen | Freigabe, Testmodus, Sperrzeit, Begrüßung, Wetter, HA-Aktionen | Zentral in HA |
| Verlauf & Diagnose | Sitzungshistorie, Test, Wiederholung, Reserve, Browserwerte zurücksetzen | Verlauf im Arbeitsspeicher |

Modelle und zentrale Helfer werden mit sichtbaren Auswahlfeldern statt überlagerten Dropdown-Menüs gewählt. HA-Statusupdates ersetzen die Bedienelemente nicht. Bei zentralen Helfern bleibt eine Auswahl bis zur HA-Bestätigung erhalten; Fehler stehen direkt am Feld. Tabs lassen sich mit Pfeiltasten, Home und End bedienen. Farben folgen dem HA-Theme beziehungsweise den vorhandenen Kiosk-Farben.
Browser-Einstellungen gelten sofort; gemeinsame Modelleinstellungen werden mit **Für Jarvis speichern** übernommen. Browser-Standardwerte ändern keine gemeinsamen Modelle.

Das [vollständige Lovelace-Beispiel](../homeassistant/templates/echo-relay-dashboard.yaml) benötigt keine private Hauszentrale. Optional **jarvis-control-panel-v1.6.0.js** zusätzlich als Ressource registrieren und `custom:jarvis-control-panel` ergänzen. Dieses zweite Panel setzt die konfigurierten Helfer und Skripte der manuellen Altinstallation voraus und gruppiert Stimme/System, Durchsagen, Hinweise/Räume und Timer/Tablet. Der Installer liefert beide Karten und alle abhängigen Module mit. Nur eine Version jedes Controllers als Ressource laden; den bisherigen Ressourceneintrag ersetzen und danach das Dashboard vollständig neu laden.

Die gemeinsame Oberfläche zeigt zusätzliche Kiosk-Steuerungen nur dort, wo deren Funktionen vorhanden sind: Hausdatenkarten, Kontext-Navigation, Rückkehr zur Hausansicht und Wikipedia-Aufbereitung gehören zur privaten Hauszentrale. Die eigenständige Karte bietet ihre funktionsfähigen Audio-, Gesprächs-, Untertitel-, Verlauf-, Kamera- und KI-Einstellungen direkt an; es gibt keine wirkungslosen Platzhalter für private Hausansichten. Die Android-App und deren Kamera-Freigabe werden weiter in der App eingerichtet. Die separate Marketplace-Seitenleiste ist keine Lovelace-Karte und wird durch diesen Ressourcentausch nicht ersetzt.

**Nachfragen:** Automatisch nutzt das Gesprächsfenster; „Bei Rückfragen“ öffnet das Mikrofon nach einer Frage in der Antwort oder einer Assist-Nachfrage. „Nur auf Assist-Anfrage“ folgt ausschließlich `continue_conversation`. Im Kiosk berücksichtigt der intelligente Modus zusätzlich dessen Wissenskontext. Sprechpause und Empfindlichkeit gelten ab der nächsten Aufnahme; Kamera-Schließzeiten ab der nächsten Infobox.

Die öffentlichen Browser-Tests umfassen DE/EN-Einstellungen, Theme/Layout, verzögerte HA-Bestätigungen, Modellspeicherung und Kameralebenszyklus. Mikrofon, Echo-Geräte und Android-WebViews müssen auf der Zielhardware getestet werden.

## Kamerafragen

Mit **Jarvis Tablet Audio 1.5.0** und **GPU Worker 1.8.0**: Außen-/Haustürkamera in den Integrationsoptionen auswählen. Fragen wie „Wer ist an der Haustür?“, „Was ist an der Haustür?“ und „Was ist draußen los?“ öffnen die zugeordnete Kamera in einer Jarvis-Kamera-Infobox im anfragenden, sichtbaren Dashboard. Gleichzeitig beschreibt Jarvis das abgerufene Einzelbild. Personen werden nur anhand sichtbarer Merkmale wie Kleidung oder mitgeführter Gegenstände beschrieben; keine Namenszuordnung oder Gesichtserkennung. Die Infobox startet die Liveansicht stumm, während die Beschreibung ein Einzelbild betrifft. Alle Bildbeschreibungen können falsch sein.

Andere Geräte, versteckte Dashboards und nativer Companion Assist öffnen die Infobox nicht automatisch. Gewöhnliche Türbefehle bleiben unverändert. Ein Fehler bei der Vorschau unterbricht die gesprochene Antwort nicht. App 0.5.0 bleibt kompatibel; alle fünf JavaScript-Dateien kopieren, Ressource aktualisieren, nach Backend-Update HA neu starten und Dashboard neu laden.

## Weiterleitung ab HA-Integration 1.4.2

Bei den Jarvis-Pipelines „Befehle bevorzugt lokal verarbeiten“ (`prefer_local_intents`) ausschalten. Jarvis prüft zuerst Kamerafragen und Dialoge und übergibt gewöhnliche Hausbefehle weiterhin an den eingebauten HA-Assistenten, bevor freie Fragen an das Sprachmodell gehen. Sonst kann HA „Wer ist an der Haustür?“ als allgemeine Anwesenheitsfrage abfangen und nur „Keins“ antworten. Auch „Was siehst du an der Haustür?“ ist jetzt enthalten. Andere Assist-Pipelines behalten ihre bisherige Einstellung.

Die Administrator-Diagnose `jarvis_tablet_audio.camera_pipeline_check` akzeptiert nur Kamerafragen und prüft die konfigurierte Intent-Pipeline ohne Aufnahme, TTS oder Wiedergabe. `speech`, `processed_locally`, `prefer_local_intents` und `errors` prüfen; Kamerafragen sollen Jarvis erreichen (`processed_locally: false`). Kein App-Update erforderlich.

## Liveansicht und Vorderseite (1.4.3)

„Was siehst du in der Vorderkamera?“ und „Was siehst du an der Vorderseite?“ verwenden die konfigurierte Außenkamera. „Zeig mir die Außenkamera“ und „Was zeigt die Vorderkamera?“ sind ebenfalls enthalten. Die gemeinsame serverseitige Zuordnung gilt für Bildbeschreibung und Vorschau.

Karte 1.0.3 und Vorschaumodul 1.1.0 starten die HA-Liveansicht stumm, ohne zusätzlichen Startknopf. Nach der Sprachantwort schließt die Infobox entsprechend „Infobox-Anzeige“ in den Jarvis-Einstellungen (Standard 30 s); die eigenständige Karte verwendet `camera_info_seconds` (15–90, Standard 30). „Länger anzeigen (+60 s)“ verlängert einmalig, insgesamt höchstens drei Minuten ab Öffnung. Schließen, eine neue Frage, Tabwechsel oder Verlassen des Dashboards beendet die Anzeige und trennt den Player. Andere HA-Karten und Aufnahmen werden dadurch nicht gestoppt. Ohne verfügbare Kamera bleibt die Fehlermeldung sichtbar, bis die Infobox schließt. Der Tablet-Feed besteht weiterhin aus aktualisierten Einzelbildern.

Versionierte JavaScript-Dateien kopieren, HA-Backend aktualisieren, HA neu starten und Dashboard neu laden. Kein APK- oder Worker-Update nötig.

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

Reine Anzeige umgeht Assist/TTS und Vision-Worker vollständig. Die Kameraübersicht zeigt bis zu drei autorisierte Feeds. Nativer Companion Assist kann diese lokale Ansicht nicht öffnen und gibt stattdessen einen Hinweis aus. Backend 1.4.4, Modul und Controller aktualisieren; HA neu starten und Dashboard neu laden. Kein APK-/GPU-Worker-Update nötig.

## KI-Modelle und Leistung (1.5.0)

In den Jarvis-Einstellungen **KI & Leistung → KI-Modelle und Leistung** öffnen. Voraussetzung: GPU Worker 1.8.0 und HA-Administrator. Das Panel zeigt installierte Text-/Bildmodelle sowie aktuell geladene Modelle und deren Ollama-GPU-Speicher. Ein Modell wird nicht allein durch Öffnen des Panels geladen.

- Gemeinsam: Textmodell und Bildmodell auf **Qwen3-VL 4B Instruct** setzen.
- Getrennt: Textmodell **Qwen3 4B Instruct**, Bildmodell **Qwen3-VL 4B Instruct**.
- Warmhaltezeit: sofort entladen oder 1/2/5/10 Minuten. Sie gilt nach Speichern für beide Anfragearten.
- Kontext: 2048/4096/8192 Tokens, ebenfalls für beide gleich. Mehr Kontext benötigt mehr GPU-Speicher.
- **Für Jarvis speichern** übernimmt die Werte zentral für alle Geräte. Änderungen gelten für die nächste Anfrage; während Jarvis verarbeitet/spricht wird nicht gespeichert. Vorhandene Systemprompts, Werkzeuge, Gesprächsverlauf-Einstellungen und Kamera-Kopplung bleiben erhalten. **Status aktualisieren** lädt den tatsächlichen Zustand neu.

[jarvis-model-settings-v1.1.0.js](../homeassistant/www/jarvis/jarvis-model-settings-v1.1.0.js) und jarvis-settings-v1.1.0.js neben den Controller nach `/config/www/jarvis/` kopieren (kein separater Ressourceneintrag). Controller 1.1.0 lädt die gemeinsamen Einstellungen. Backend 1.5.0 und Worker 1.8.0 verwenden, nach Backend-Installation HA neu starten und Dashboard neu laden. Nur bereits installierte, erlaubte Modelle werden angeboten. Keine automatischen Downloads. Modellwahl startet die Kamera nicht neu. Gemeinsame Text-/Vision-Nutzung verwendet gleichen Modellnamen, Kontext und Warmhaltezeit; Ollama auf ein Modell begrenzen. STT und TTS bleiben unverändert. Kein APK-Update nötig.

`jarvis_tablet_audio.model_settings` mit `action: get` liefert eine Revision. `action: set` erwartet Revision, `text_model`, `vision_model`, `keep_alive` und `num_ctx`. Nichtadministratoren sowie veraltete oder nicht unterstützte Werte werden abgewiesen. Worker-Zugangsdaten und Systemprompts werden nicht zurückgegeben.

## Änderungen

- v1.1.0: gemeinsame farb- und tastaturgerechte Einstellungen, direkte Modell-/Helferauswahl, Mikrofon-, Gesprächs-, Untertitel-, Verlaufs- und Reserveeinstellungen. Optionales Bedienpanel 1.6.0 gruppiert Hausfunktionen.
- v1.0.5: zentrale Modellauswahl, Kontext, Warmhaltezeit und geladene Modelle.
- v1.0.4: stille Kameraansicht und autorisierte Kameraübersicht; Bildbeschreibung nur bei Sichtfragen.
- v1.0.3: stumm gestartete Live-Infobox, Schließzeit nach Sprachausgabe, Player-Bereinigung und Verlängerung.
- v1.0.2: Kameravorschau auf dem anfragenden Dashboard, gemeinsame Backend-Zuordnung und Leserechte.
- v1.0.1: Rufwort-, Sprach-, Verarbeitungs-, Puffer- und Wiedergabeanzeigen; keine Sprecheridentität.
- v1.0.0: Mikrofonzyklus, bewusste Vordergrundaufnahme, Echo-Relay-Status-/Befehlsvertrag und optionale Reserve. Keine privaten IDs oder Hauszentrale-Abhängigkeit. Einzelne Backend-Fehler können in der Sprache von HA erscheinen.
