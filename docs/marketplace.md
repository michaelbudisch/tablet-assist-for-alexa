# TAFA-Integration über Marketplace (ohne TAFA-App)

[English](en/marketplace.md) · [Projekt](../README.de.md) · [Empfohlene App-Installation](app.md)

**Alternative Installationsart:** Marketplace installiert nur die HA-Integration `tablet_assist_for_alexa`, **nicht** die TAFA-App mit integriertem CPU-Piper/Whisper und Control Center. Für neue Nutzer mit Home Assistant OS ist der [TAFA-App-Einrichtungsweg](setup-guide.md) normalerweise einfacher. **Die gleiche Integration niemals gleichzeitig durch TAFA-App und Marketplace verwalten.**

## Voraussetzungen

- Home Assistant Core ab **2026.11** mit kompatibler Plattform; HA-Konfiguration vorab sichern.
- Ein erreichbarer **externer CPU-Sprachserver** mit kompatibler Piper-HTTP-API und Wyoming-Whisper (zum Beispiel [TAFA-Proxmox](proxmox.md)).
- Die signierte [TAFA Device Bridge](../android/README.de.md) für native Android-Aufnahme und Bluetooth-Ausgabe.
- Optional: [GPU Worker](worker.md), HA-Ollama-Konversationsagent und Alexa-MP3-Durchsagen.

Marketplace stellt die gemeinsame TAFA-Integration bereit. **Ein extra Jarvis Tablet Audio oder Jarvis Speech Router wird bei Neuinstallationen nicht benötigt.** Die HA-Integration, das TAFA-Dashboard und die Device-Bridge-Funktionen gehören zum zusammengeführten Projekt; der eigenständige TAFA-App-**Control Center** und ihre CPU-Prozesse sind in diesem Installationsweg **nicht** enthalten.

## Installation

1. **Einstellungen → Marketplace → Über Link hinzufügen**: `https://github.com/michaelbudisch/tablet-assist-for-alexa` mit Kategorie **Integration** auswählen.
2. **TAFA** installieren, HA Core neu starten und unter **Geräte & Dienste → Integration hinzufügen → TAFA** einrichten.
3. Piper-HTTP-Adresse des **CPU-Servers** eintragen (z. B. `http://CPU-SERVER:5000`).
4. Unter **HA → Geräte & Dienste → Wyoming Protocol** den CPU-Server an TCP **10300** hinzufügen und seine `stt.*`-Entität in den TAFA-Integrationsoptionen auswählen. Der reine Piper-HTTP-Endpunkt ist kein Wyoming-STT.
5. Unter **Einstellungen → Sprachassistenten** eine **TAFA Lokal**-Pipeline mit **Tablet Assist Sprachrouter**, **Tablet Assist Gesprächsrouter** und **Tablet Assist Stream** erstellen beziehungsweise prüfen.
6. Optional die GPU-/Ollama-Entitäten in HA ergänzen. Danach die Android Device Bridge und einen Bluetooth-Lautsprecher verbinden und eine echte Frage testen.

[Marketplace in HA öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Integration starten](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## CPU/GPU und Sicherheit

**CPU-Fallback:** Externe Wyoming-STT-Entität und Piper müssen erreichbar sein, auch wenn GPU-Whisper/Qwen nicht verfügbar sind. GPU-TTS, GPU-STT und Ollama sind unterschiedliche Dienste. Freie Textantworten über Ollama haben **keinen automatisch eingerichteten CPU-LLM-Fallback**. Ohne CPU-/GPU-Agenten bleiben lokale HA-Intents nutzbar.

**Updates:** Die Marketplace-Integration nur über Marketplace aktualisieren; kein paralleler TAFA-App-Installer. Eine vorhandene Altintegration `jarvis_tablet_audio` nicht ungeprüft löschen oder überschreiben; Migration und eigene Automatisierungen separat prüfen. Keine Worker-Ports öffentlich freigeben. [Sicherheit](security.md).

**Versionsstand:** Die im Repository enthaltene Integration wird über `custom_components/tablet_assist_for_alexa/manifest.json` versioniert; die App-Version ist unabhängig. Die tatsächliche Installation und Audiowiedergabe auf eigener Hardware prüfen.
