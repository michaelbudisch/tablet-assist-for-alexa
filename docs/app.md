# TAFA Home-Assistant-App installieren

[English](en/app.md) · [Projektübersicht](../README.de.md) · [Vollständiger Einrichtungsweg](setup-guide.md) · [Control Center – Funktionen und Grenzen](control-center.md) · [Eigene Dashboards/Infoboxen](dashboard-integration.md) · [WebSocket-Sprachschalter](dashboard-voice-control.md)

TAFA stellt ein **Control Center**, eine gemeinsame HA-Integration und optional CPU-Piper/Faster-Whisper bereit. Voraussetzung: **Home Assistant OS ab 2026.11** mit Apps auf `amd64` oder `aarch64`.

## Neuinstallation

1. Home Assistant sichern. **Einstellungen → Apps → App installieren → Repositories** öffnen und `https://github.com/michaelbudisch/tablet-assist-for-alexa` hinzufügen.
2. **TAFA** installieren und starten. Eine neue Installation verwendet `speech_mode=setup`, **nicht** bereits den lokalen Modellmodus. Im Control Center unter **Einstellungen** bewusst **Lokal** (Piper/Whisper in der TAFA-App) oder **Extern** (bestehender kompatibler Sprachserver) wählen. Im Modus `setup` werden keine CPU-Modelle heruntergeladen.
3. Für **Extern** die Piper-HTTP-Adresse im Tab **Verbindungen → CPU-Fallback** eintragen. Bei Wyoming-Whisper die **Wyoming Protocol**-Integration unter HA **Geräte & Dienste** hinzufügen (CPU-Host, Port 10300) und danach in **TAFA → Verbindungen** die CPU-`stt.*`-Entität auswählen. Im Modus **Lokal** werden die Modelle nach Auswahl und Neustart der App geladen.
4. TAFA richtet `custom_components/tablet_assist_for_alexa` ein. **Home Assistant Core einmal neu starten** und unter **Geräte & Dienste** prüfen, ob die TAFA-Integration geladen ist. Bei Bedarf die TAFA-App neu starten. **Keine zweite Marketplace-Kopie** installieren.
5. Unter **Einstellungen → Sprachassistenten** die Pipeline **TAFA Lokal** prüfen: **Tablet Assist Sprachrouter** (STT), **Tablet Assist Gesprächsrouter** (Gespräch), **Tablet Assist Stream** (TTS). Fehlende Komponenten erst in TAFA/HA konfigurieren; vorhandene Pipelines werden nicht überschrieben.
6. Die [signierte TAFA Device Bridge](../android/README.de.md) auf Android installieren, verbinden und native Sprache/Ausgabe testen. Weitere Schritte im [Einrichtungsleitfaden](setup-guide.md).

## Bereiche des Control Centers

| Bereich | Inhalt |
| --- | --- |
| **Übersicht** | Status des Sprachwegs und Hinweise |
| **Verbindungen** | **Schnelleinrichtung per JSON**, GPU-PC-IP/Schnellprüfung, GPU-Whisper-/Qwen-/Ollama-Verbindungen, CPU-Piper/Wyoming und Alexa-MP3/HTTPS |
| **Einstellungen** | Sprachmodus, Routing, Stimme, Gesprächsverhalten und optionale Funktionen |
| **Geräte & Multiroom** | Tabletregistrierung, Benutzer, Raum- und Kamera-Freigaben |
| **Wartung & Hilfe** | Diagnose, Backend/Modelle und Neustart |
| **Jetzt sprechen** | Separater **Browser-Sprachtest**: Stumm/Rufwort/Immer an, Transkript, Antwort und Zeiten; HTTPS/localhost für Browser-Mikrofon erforderlich |

**Wichtig:** Eine erfolgreiche TCP-/HTTP-Prüfung beweist nur Erreichbarkeit, **keine** erfolgreiche Spracherkennung oder Bluetooth-Ausgabe. Der Browser-Test **Jetzt sprechen** spielt im Browser ab und ist von der nativen Android/Echo-Ausgabe getrennt. Die Android-App bietet ihren eigenen Rufwortdienst, der unabhängig vom offenen HA-Dashboard läuft.

## Funktionen & Datenquellen – ohne JSON

Unter **TAFA Control Center → Funktionen & Datenquellen** erscheinen alle verfügbaren Module. Neue Module stehen nach TAFA-Updates zur Auswahl, ohne bestehende Dashboard-Kacheln oder Automationen zu überschreiben.

1. Funktion öffnen, beispielsweise **Heizöl & Tank**.
2. Home-Assistant-Sensor anhand seines Anzeigenamens auswählen. TAFA prüft den Entitätstyp und die Maßeinheit.
3. **Zuordnungen speichern**: Die Sprachabfrage verwendet den Sensor. Das integrierte Dashboard nutzt dieselbe Datenquelle, sofern keine eigene Zuordnung besteht.
4. **Zum TAFA-Dashboard hinzufügen** aktiviert ein noch nicht angezeigtes Modul – die bestehenden Kacheln bleiben erhalten.
5. Fehlende Integrationen lassen sich später unter **Einstellungen → Geräte & Dienste** installieren. Andere Funktionen bleiben verfügbar.

Alexa-Ankündigungen werden ebenfalls grafisch zugeordnet. Dafür muss in Home Assistant ein passender notify-Dienst existieren. Weitere Alexa-Räume können angelegt werden; native Tablets bleiben unter **Geräte & Multiroom**.

Die bisherigen internen Formate sources_json und rooms_json bleiben aus Kompatibilitätsgründen erhalten, sind aber nicht mehr für die normale Einrichtung erforderlich.

**Updates:** TAFA speichert Dashboard-Einstellungen unabhängig vom Programmcode. Bei älteren Konfigurationen werden gültige Einstellungen einzeln übernommen. Vor einem neuen Speichern wird die vorherige Konfiguration gesichert. Das private Lovelace-Dashboard und bestehende Automationen werden nicht verändert.

## Updates und vorhandene Installationen

TAFA aktualisiert nur die von **dieser App** verwaltete, unveränderte Integration und legt vor dem Austausch eine Sicherung unter `<HA-Konfiguration>/.tafa/rollback` an. Von Marketplace/HACS oder manuell verwaltete Integrationen werden nicht still überschrieben. Nach Backend-Updates HA Core einmal neu starten. Bereits vorhandene Automatisierungen, eigene Dashboards und andere Assist-Pipelines nicht automatisch löschen oder migrieren.

Für einen dedizierten externen CPU-Server gilt [Proxmox](proxmox.md); für optionale GPU-KI [Worker](worker.md); für die reine Integration ohne diese App [Marketplace](marketplace.md). Die [historische Jarvis-Anleitung](home-assistant.md) ist **kein** Neuinstallationsweg.

**Sicherheit:** CPU-/GPU-Dienste nur im vertrauenswürdigen LAN erreichbar machen. Zusätzliche TAFA-API-Tokens für die neuen lokalen Worker-Endpunkte sind nicht erforderlich, die normale Home-Assistant-Anmeldung und Berechtigungen jedoch weiterhin.
