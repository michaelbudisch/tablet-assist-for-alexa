# TAFA Control Center – Zuständigkeiten, Einrichtung und Erweiterung

[English](en/control-center.md) · [Projekt](../README.de.md) · [Einrichtung](setup-guide.md) · [Eigene Dashboards entwickeln](dashboard-integration.md)

Das **TAFA Control Center** ist die zentrale Konfigurationsoberfläche der TAFA Home-Assistant-App unter **Einstellungen → Apps → TAFA → Benutzeroberfläche**. Es richtet den *Sprachassistenten* ein. Ein TAFA-Dashboard ist dafür **nicht erforderlich**. Du kannst ausschließlich TAFA Device Bridge mit der HA-Sprachpipeline betreiben und dein bestehendes Home-Assistant-Dashboard weiterbenutzen.

## Drei getrennte Ebenen

| Ebene | Zuständigkeit | Nicht zuständig für |
| --- | --- | --- |
| **Control Center + HA-Integration** | Sprachpipeline, STT, Gesprächsagent, CPU/GPU-Routing, TTS, Datenquellen, Tabletregistrierung, Raum- und Audiozuordnung | Infobox-Layout, Animationsstil, Infobox-Anzeigedauer eines fremden Dashboards |
| **TAFA Device Bridge (Android)** | Rufworterkennung, Mikrofon, native Assist-Sitzung, Bluetooth- und Tablet-Audioausgabe | Darstellung einer Web-Infobox |
| **Optionales Dashboard** | Visualisierung von Sprachzuständen und Antworten, Infobox-Animation, Dauer, Navigation, Karten und Layout | Eigenständige zusätzliche STT-/KI-Pipeline |

Das integrierte **TAFA Dashboard** ist optional. Das historische private **TAFA-Hausdashboard** enthält noch den Menüpunkt **Jarvis**; dieser ist eine Bezeichnung aus der Entwicklung und kein zweiter Sprachassistent. Das **TAFA Dashboard DEV** ist eine separate Entwicklungsoberfläche. Seine Funktionen nicht mit dem privaten Jarvis-Menü gleichsetzen und keine privaten Haushaltsentitäten in die öffentliche Distribution kopieren.

## Control Center: Bereiche

Die Bezeichnungen können sich zwischen App-Versionen geringfügig ändern.

| Bereich | Wozu er dient |
| --- | --- |
| **Übersicht** | Zustand der verbundenen Dienste, Sprachweg, Diagnosehinweise |
| **Verbindungen** | GPU-Worker-Verbindungen und JSON-Import, Ollama/Qwen, Whisper/Wyoming, CPU-Piper und externe Audio-/HTTPS-Verbindungen |
| **Einstellungen** | Sprachmodus, Routing, Stimme, Gesprächsverhalten und KI-Optionen |
| **Funktionen & Datenquellen** | HA-Wetter, Energie, Wärmepumpe, Heizöl, Einkauf, Müll usw. optional mit Sensoren verknüpfen; kein Dashboard-Zwang |
| **Geräte & Multiroom** | Android-Tablets registrieren, Benutzer und Räume koppeln, Audiogeräte und Kamera-Freigaben verwalten |
| **Wartung & Hilfe** | Komponentenstatus und Diagnose, Wartungsschritte |
| **Jetzt sprechen** | **Browser-Test** der Spracherkennung und Antwort; **kein** Ersatz für einen Test der Android-/Bluetooth-Ausgabe |

### Nur TAFA-Sprach-KI verwenden – ohne TAFA-Dashboard

1. TAFA-App **oder** die Marketplace-Integration installieren, nicht beide Installationswege parallel. HA-Integration und benötigte Sprachdienste einrichten.
2. Im **Control Center → Verbindungen** die tatsächlich verwendeten CPU-/GPU-Dienste hinterlegen und deren Status prüfen. Wyoming und Ollama müssen gegebenenfalls separat in Home Assistant verfügbar sein.
3. Unter **Einstellungen** die HA-Sprachpipeline und Gesprächsoptionen festlegen. Der Browser-Test **Jetzt sprechen** prüft einen anderen Ausgabeweg als die Android-App.
4. Für ein Android-Tablet unter **Geräte & Multiroom** einen eigenen aktiven **Nicht-Admin-HA-Raumnutzer** und eine Geräte-/Raumkopplung einrichten. Den Sprachweg mit der **TAFA Device Bridge** testen.
5. Das vorhandene HA-Dashboard verwenden, ein eigenes bauen oder die optionale TAFA-Dashboard-Karte hinzufügen. **Keine zusätzliche Jarvis-Pipeline installieren.**

Optional gespeicherte Datenquellen bereichern Sprachantworten, sind aber keine Pflicht. Fehlende Sensoren können später ergänzt werden.

## Was gehört in die Einstellungen eines Dashboards?

**Lokal pro Anzeige:** Auswahl, ob das Dashboard überhaupt ein Sprachgerät anzeigen soll; zugeordnetes Gerät; Infobox-Dauer, Position, Größe, Layout, Animation, Themenfarben, Navigation, Bilder und Darstellungsmöglichkeiten. Ein PC ohne zugeordnetes Tablet kann als reiner Betrachter geöffnet bleiben.

**Zentral in TAFA:** die eigentliche Frage-/Antwort-Verarbeitung, Modelle, STT-/TTS-Routing, Raumzuordnung und gerätespezifischer Sprachstatus. Ein Dashboard fragt diese Informationen ab, statt die Logik erneut zu implementieren.

Das integrierte Dashboard speichert sein Präsentationsschema über Home Assistant; ein eigenes Dashboard darf seine Darstellungspräferenzen separat verwalten. Beide dürfen die Core-Audio- und KI-Konfiguration nicht still verändern.

## Multiroom: wichtige Regeln

- Eine **TAFA Device Bridge** besitzt eine eigene 32-stellige Registrierungs-ID, die **nicht** mit der HA-Geräteregister-ID identisch ist.
- Im Regelfall **ein eigener Nicht-Admin-HA-Benutzer pro Tablet/Raum**. Die Anmeldung der **Companion-App** kann davon abweichen; die visuelle Gerätezuordnung muss dann ausdrücklich stimmen.
- Ein HA-Administratorkonto am PC darf nicht automatisch das einzig vorhandene Tablet übernehmen. Auch bei nur einem registrierten Gerät ist ein PC ohne ausgewählte Geräte-ID **passiv**.
- Eine Antwort darf nur auf einem Dashboard des richtigen Tablets erscheinen. Gleiche HA-Benutzer-IDs auf mehreren Browsern reichen als Zuordnung nicht aus.
- Eine Registrierung der Rufworterkennung beweist noch **keine** funktionsfähige Audio-/Bluetooth-Raumkopplung.

Die komplette Einrichtung: [Multiroom – mehrere Tablets](../homeassistant/examples/MULTIROOM.de.md).

## Erweiterung: eigenes Dashboard, Infoboxen, Sprachstatus

Die TAFA-Integration bietet **authentifizierte, lesende WebSocket-Schnittstellen** für die Geräteidentität und den Antwortstrom. Damit lässt sich beispielsweise die Frage **„Wer war Albert Einstein?“** als Text, Bildkarte oder auf anderem Wege anzeigen. TAFA entscheidet über *die Antwort*, das Dashboard über *die Darstellung*.

- **[Entwicklerleitfaden: eigene Dashboards und Infoboxen](dashboard-integration.md)** – Ereignisschema, gerätespezifischer Antwortstrom, WebSocket-Beispiel, Multiroom-Schutz und Fehlerbehebung
- **[TAFA-Sprachsteuerung im eigenen Dashboard](dashboard-voice-control.md)** – Standard-HA-Entitäten zum Stummschalten und für den Sprachmodus
- **[Datenquellen und Sprachbefehle](data-sources.md)** – optionale HA-Sensoren
- **[TAFA-App installieren](app.md)** und **[Einrichtung](setup-guide.md)**

Die visuellen WebSocket-Endpunkte sind noch relativ neu: Änderungen an ihren Payloads sollten dokumentiert, rückwärtskompatibel und mit mehreren gleichzeitig geöffneten Dashboards getestet werden.

## Häufige Missverständnisse

| Beobachtung | Richtig einordnen |
| --- | --- |
| Browser-Test antwortet, Echo bleibt still | Browser-Audio und nativer Bluetooth-/Tablet-Player sind getrennte Wege |
| Infobox nur im PC-Browser | Prüfen, ob das Tablet-Dashboard an **seine eigene Geräte-ID** gebunden ist, und ob das Ereignis dem Gerät zugeordnet wurde |
| Kugel animiert auf mehreren PCs/Tablets | Anzeigen ohne lokale Gerätezuordnung müssen im Idle bleiben; keine automatische PC-Kopplung |
| Wetterkarte erscheint, Wissenskarte nicht | Zusätzlich lokale/gespeicherte Präsentationseinstellungen prüfen; Wissenskarten können eigens ein-/ausgeschaltet sein |
| TAFA Dashboard DEV zeigt keine Assistenten-Karte | Separates **Frontend-/Einbindungsproblem**, kein Grund, die private Jarvis-Seite ins Control Center zu duplizieren |
| Infobox wird durch HA-Automatisierung geöffnet | Automatisierung ist ein **Auslöser für eine Darstellung**, nicht die allgemeine Sprach-/KI-Engine |

**Updates und Datenschutz:** Keine Tokens, privaten Geräte-IDs, Home-Assistant-Benutzer-IDs oder Haushalts-Sensorzuordnungen in Git-Quellcode und öffentliche Beispiele übernehmen. Bestehende Dashboards und Automationen nicht automatisch überschreiben.