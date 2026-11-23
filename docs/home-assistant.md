# Home Assistant und Android-Tablet (manuelle Altinstallation)

[English](en/home-assistant.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Für Neuinstallationen ist die [Marketplace-Integration](marketplace.md) empfohlen. Die folgenden Schritte sind nur der alternative Altinstallationsweg; seine Oberfläche und Sprachbefehle bleiben deutsch.

Die bereinigten Integrationen und Vorlagen befinden sich direkt im Repository.

## Installation auf einer neuen Instanz

1. Backup erstellen. In Home Assistant Wyoming hinzufügen: IP des CPU-Sprachservers, Port 10300. Die resultierende STT-Entity notieren. Optional GPU-Wyoming hinzufügen.
2. `homeassistant/config.example.json` nach `homeassistant/config.local.json` kopieren und eigene Werte eintragen. `gpu_host` und `gpu_stt` ohne GPU auf den Platzhalterwerten lassen. `llm_agent` ohne LLM unverändert lassen. Pipeline-ID leer lassen, bis die Assist-Pipeline angelegt ist.
3. Vorlagen in einem neuen, leeren Staging-Verzeichnis rendern:

```bash
bash homeassistant/install.sh config.local.json ./staging
```

4. Verzeichnisse `custom_components/`, `www/` sowie `packages/jarvis.yaml` aus dem Staging-Verzeichnis in `/config` kopieren, ohne fremde Dateien zu überschreiben. `configuration.yaml` nur ergänzen (bestehende `homeassistant:`-Sektion nicht duplizieren):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
   Vorhandene gleichnamige Helfer/Automationen müssen vorab auf Konflikte geprüft werden. Der Installer ist **kein** Upgrade-Skript für das bestehende System.
5. In `secrets.yaml` den auf dem Sprachserver generierten Wert lokal als `piper_api_token` eintragen. Keine echten Schlüssel in Git. HA-Konfiguration prüfen, dann Neustart.
6. Zwei Integrationen über Einstellungen → Geräte & Dienste hinzufügen: **Jarvis Speech Router** und **Jarvis Tablet Audio**. GPU-Token im Integrationsdialog nur bei vorhandenem Worker eintragen. Die STT-Entity-ID bzw. TTS-Entity-ID kontrollieren.
7. Unter Einstellungen → Sprachassistenten eine neue Pipeline mit deutscher Sprache anlegen: Jarvis-Gesprächsrouter, Jarvis Sprachrouter als STT, Jarvis Tablet Stream als TTS. Lokale Intents bevorzugen. In der Companion App diese Pipeline auswählen. Nur wenn die default pipeline nicht Jarvis sein soll, Pipeline-ID im Konfigurations-JSON ergänzen und Frontend-Dateien neu rendern/kopieren.
8. Für ein eigenes Dashboard folgende JS-Ressourcen als Module registrieren:
   - `/local/jarvis/jarvis-dashboard-assist-v1.4.0.js`
   - `/local/jarvis/jarvis-bt-keepalive-v1.1.0.js`
   - `/local/jarvis/jarvis-control-panel-v1.6.0.js`
   - `/local/jarvis/echo-relay-assist-card-v1.2.0.js`
   Die Module `jarvis-settings-v1.1.0.js`, `jarvis-model-settings-v1.1.0.js` und `jarvis-camera-preview-v1.2.0.js`, `jarvis-proactive-v1.0.0.js` müssen ebenfalls in `/config/www/jarvis/` liegen; sie werden automatisch importiert und benötigen keinen eigenen Ressourceneintrag.
   Den Inhalt der Vorlage `jarvis-dashboard.yaml` in den YAML-Editor des neuen Dashboards übernehmen. Keine vollständige private Hauszentrale enthalten. Kiosk/App-Vollbild im Gerätebrowser einstellen.
9. Native Sprachaufnahme testen: zunächst bekannte HA-Intents, dann optional LLM-Wissensfrage, anschließend Streaming und Klangprofil wechseln. Bei fehlendem LLM sind allgemeine KI-Fragen nicht möglich, lokale Intents bleiben verfügbar.

## Native Ausgabe über Amazon Echo (Bluetooth)

1. Tablet mit einem eigenen berechtigten Home-Assistant-Konto anmelden und die Companion App einrichten. Mikrofonberechtigung nur für die beabsichtigte Assist-Nutzung erteilen.
2. In der Alexa-App für den betreffenden Echo Bluetooth-Kopplung starten oder am Echo nach Bluetooth-Kopplung fragen. Auf dem Tablet in den Android-Bluetooth-Einstellungen den Echo auswählen und als Medienaudio verbinden.
3. In der Home-Assistant-App die Jarvis-Assist-Pipeline auswählen und — sofern Gerät und App es unterstützen — die native Wakeword-/Assistentenfunktion einrichten. Nicht jedes Android-Gerät unterstützt dauerhaftes Wakeword-Hören.
4. Eine normale Assist-Frage stellen. Die Aufnahme erfolgt am Tablet; die Ausgabe läuft über Androids Medienaudio zum gekoppelten Echo. Der Echo bleibt ein normaler Alexa-Lautsprecher. Das Echo-Mikrofon ist **nicht** die Eingabe für lokale Assist-Anfragen.
5. Optional die Bluetooth-Keepalive-Karte auf dem Tablet nach Bedarf starten. Sie spielt einen lautlosen Audioloop ab; verhindert Verbindungsabbruch nicht auf allen Geräten, kann zusätzliche Akkulast verursachen und endet beim echten Reload. Ein Test der normalen Alexa-Nutzung und des Audio-Routings ist erforderlich. Bei Störungen Loop stoppen.

Die Bluetooth-Ausgabe benötigt keine öffentlich bereitgestellte MP3-Datei. Die folgende Multiroom-Durchsage ist eine getrennte optionale Funktion.

## Alexa-Durchsagen (optional)

`rooms` in der lokalen JSON-Konfiguration pro vorhandenen Raum mit `media_player`, `notify` und `dnd` konfigurieren (Beispiel unten). Die Notify-Entity muss SSML-Audio unterstützen. Nur bei vorhandener kompatibler Alexa-Integration und gültiger HTTPS-Audio-Basis funktioniert diese Funktion. Keine üblichen HA-Sprachantworten durch einen separaten Alexa-Bridge-Poller doppeln.

```json
{
  "buero": {
    "media_player": "media_player.echo_buero",
    "notify": "notify.echo_buero_sprechen",
    "dnd": "switch.echo_buero_bitte_nicht_storen"
  }
}
```

Nicht konfigurierte Räume sind nur Platzhalter und dürfen keine Ausgabe erzeugen. Der HTTPS-Proxy muss nur zeitlich begrenzte 32-stellige MP3-Dateinamen ausliefern, keine anderen Routen. Nicht für vertrauliche Nachrichten verwenden. Raum-Ruhepläne konfigurieren. Automatische Hinweise starten ausgeschaltet. `event_sources` kann optionale Sensor-IDs ersetzen; Hinweise mit fehlenden Quellen werden nicht installiert. Waschmaschine setzt die passende Zustandslogik einer vorhandenen Waschgang-Erkennung voraus, nicht irgendeinen Leistungssensor. Statuswechsel und Einheiten der übrigen Quellen prüfen. Das Erinnerungsmodul unterstützt **einen** aktiven Termin.

See [Echo Relay Lovelace settings](echo-relay-dashboard.md) for the shared settings modules, camera/model prerequisites and the complete portable dashboard example.
