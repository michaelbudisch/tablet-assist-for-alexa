# Marketplace – TAFA

[English](en/marketplace.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Home Assistant Core ab 2026.11; Entwicklungsvorschau 0.3.1. Auf einer Testinstanz beginnen und die funktionierende Altinstallation nicht überschreiben.

**Neu in 0.3.1:** Lokale Absichtserkennung, frei konfigurierbare Wetter-, Bring!-, Abfall-, Heizungs- und Energiedaten sowie ein persistenter Erinnerungsdialog. [Datenquellen und Sprachbefehle](data-sources.md).

**Neu:** Kontextbezogene Folgefragen und freiwillige, administrativ freigegebene Lernzuordnungen. [Anleitung](data-sources.md).

## TAFA Home-Assistant-App (experimentell)

[![TAFA-App-Repository hinzufügen](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmichaelbudisch%2Ftablet-assist-for-alexa)

Unter Home Assistant OS: Einstellungen → Apps → App installieren, diese Repository-Adresse hinzufügen, **TAFA** installieren, starten und die Weboberfläche öffnen. Die experimentelle Einrichtungs-App (0.1.0) enthält die öffentlichen Basis- und Raum-Audio-Integrationen. Fehlende Backend-Dateien werden über die Administrator-Ingress-Oberfläche nach ausdrücklicher Bestätigung installiert; vorhandene Integrationen werden nie überschrieben. Externe Sprachserver und die Android Device Bridge bleiben separat. Nach der Dateiinstallation HA neu starten und beide Integrationen unter Geräte & Dienste konfigurieren. Siehe [App-Installation](app.md).

Marketplace ist ein separater Installationsweg und installiert weiterhin nur die Basisintegration. Das private Dashboard ist bei beiden Wegen ausgeschlossen. Der Neuinstallationstest steht noch aus; dies ist noch kein produktionsreifer, zusammengeführter Backend-Release.

## Marketplace-Umfang und Backend-Fahrplan

Der aktuelle Link installiert ausschließlich die Basisintegration `tablet_assist_for_alexa`. Das separate Backend `jarvis_tablet_audio` (Multiroom, Geräteregistrierung, native Rufwortweiterleitung und Kamera-/Vision-Schnittstellen) wird darüber nicht installiert. Marketplace unterstützt eine Integration pro Repository. Ziel ist eine einzige konfigurierbare Integration, in die diese Funktionen portiert und getestet werden, einschließlich dokumentierter Kompatibilität mit Device Bridge 1.0.0. Externe CPU-/GPU-Sprachserver und die Android-APK bleiben separate Installationen. Privates TAFA-Dashboard, dessen Ressourcen und Haushaltskonfiguration sind ausgeschlossen. Bestehende Systeme nicht überschreiben; keine automatische Migration voraussetzen. Siehe [Backend-Fahrplan](backend-roadmap.md).

## 1. Sprachserver vorbereiten

[CPU / Proxmox](proxmox.md) einrichten. Der [GPU-Worker](worker.md) ist optional. Die Wyoming-Integration für den CPU-Sprachserver hinzufügen (Host, TCP 10300). Bei GPU-STT eine zweite Wyoming-Integration hinzufügen und deren Entität notieren.

## 2. Über Marketplace installieren

1. Einstellungen → Marketplace → Über Link hinzufügen.
2. `https://github.com/michaelbudisch/tablet-assist-for-alexa` eingeben, ggf. Kategorie Integration wählen und GitHub verbinden.
3. Verfügbare Version installieren. Das Repository enthält eine Integration direkt in `custom_components/tablet_assist_for_alexa/` sowie `hacs.json`. Manuelles Kopieren entfällt.
4. Einstellungen → Geräte & Dienste → Integration hinzufügen → Tablet Assist for Alexa. Bei Aufforderung neu starten.

[Im Home Assistant öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration) · [Integration hinzufügen](https://my.home-assistant.io/redirect/config_flow_start/?domain=tablet_assist_for_alexa)

## 3. Integration ohne YAML einrichten

| Feld | Beispiel / Erklärung |
|---|---|
| Piper-Adresse | `http://speechserver.local:5000` (eigenen internen Host verwenden) |
| CPU-Wyoming-Spracherkennung | CPU-STT-Entität auswählen |
| GPU-Streaming-Adresse | Optional, z. B. `http://gpu.local:10502` |
| GPU-API-Schlüssel | Optional, aus lokaler Worker-Konfiguration |
| GPU-Wyoming-Spracherkennung | Optionale zweite STT-Entität |
| GPU-STT-Host | Optionaler Hostname für Schnelltest auf Port 10300 |
| KI-Konversationsagent | Optionaler vorhandener HA-KI-Agent, nicht dieser Router selbst |
| Hardwareprofil | Automatisch = GPU bevorzugt, Homeserver = CPU |
| Live-Klangprofil | Natürlich / Studio / Klar |
| Stimmvariante | Standard oder 1–9, entsprechend vorbereiteter Worker nötig |
| Gesprächsmodus | Manuell / Intelligent / Automatisch |

Adressen und Schlüssel werden lokal im Konfigurationseintrag gespeichert. Über das Integrationsmenü neu konfigurieren. Piper muss bei der Einrichtung erreichbar sein; GPU und KI sind optional. Einstellungen gelten für die Integration, nicht pro Tablet.

**Sprache:** Bedienoberfläche und Dokumentation sind deutsch und englisch. Die mitgelieferte Sprachpipeline, Sprachbefehle und Standardmodelle sind weiterhin deutsch. Englische Sprachverarbeitung ist nicht Bestandteil dieser Version.

Assist-Pipeline mit deutscher Sprache auswählen/anlegen: Tablet Assist Gesprächsrouter, Tablet Assist Sprachrouter, Tablet Assist Stream (oder Piper). Lokale Intents bevorzugen; allgemeine Wissensfragen benötigen einen konfigurierten KI-Agenten. In der Android-App diese Pipeline auswählen. Siehe [Tablet und Bluetooth](home-assistant.md#native-ausgabe-über-amazon-echo-bluetooth). Echo ist nur der Ausgabelautsprecher, nicht das Mikrofon.

## 4. Eigene Sprachzentrale (automatisch)

Nach erfolgreicher Integrationseinrichtung erscheint **Tablet Assist** in der Home-Assistant-Seitenleiste (Pfad `/tablet_assist_for_alexa`). Dies ist eine integrierte eigene Seite, kein zu bearbeitendes Lovelace-Dashboard. Sie benötigt weder die private Hauszentrale noch deren Helfer und JS-Ressourcen. Sie bietet Assist-Start, Status der Sprachdienste, Links zur Konfiguration (Administratoren), Bluetooth-Keepalive und Durchsagen an konfigurierte Räume. In der Companion-App wird der native Assist geöffnet; im Browser ist der Standard-Dashboard-Assist der Ausweichweg. Wähle die richtige Pipeline. Die Seite verwendet die HA-Oberflächensprache. Beim Entladen der Integration wird der Sidebar-Eintrag entfernt. Die tatsächliche Darstellung und native App-Auslösung müssen auf Zielgeräten geprüft werden.

## 5. Optionale Alexa-MP3-Durchsagen

Für Bluetooth nicht erforderlich. [Nginx, DuckDNS und Certbot](nginx-proxy.md) einrichten sowie eine kompatible Notify-Integration, die SSML-Audio unterstützt.

- MP3-API-Adresse: intern `http://speechserver.local:5001`.
- MP3-API-Schlüssel: aus der geschützten lokalen Sprachserver-Konfiguration.
- Öffentliche HTTPS-Audioadresse: eigener zertifikatsgesicherter Host, z. B. `https://audio.example.org`.
- Raumzuordnung (JSON): eigene Notify-Entitäten und optional DND-Schalter und Ruhezeitpläne eintragen.

```json
{
  "Büro": {
    "notify": "notify.echo_buero_sprechen",
    "dnd": "switch.echo_buero_bitte_nicht_storen",
    "quiet": "schedule.echo_buero_ruhe"
  }
}
```

Gültige Raumschlüssel: Büro, Wohnzimmer, Badezimmer, Schlafzimmer, Kinderzimmer (auch bei englischer Oberfläche). Weitere Räume sind noch nicht unterstützt. Konfigurierte DND- und Ruhezeit-Entitäten müssen aus sein; fehlende oder nicht verfügbare konfigurierte Entitäten blockieren die Durchsage. Ein optionales Feld nur weglassen, wenn diese Einschränkung bewusst nicht gewünscht ist. Nicht konfigurierte Räume erhalten keine Ausgabe. Keine vertraulichen Nachrichten; die HTTPS-Links sind 15 Minuten abrufbar.

Die Aktion kann aus der Sprachzentrale, Automationen und Entwicklerwerkzeugen genutzt werden:

```yaml
action: tablet_assist_for_alexa.announce
data:
  text: "Die Waschmaschine ist fertig."
  rooms:
    - Büro
```

Auch der deutsche Durchsagedialog nutzt diese Aktion. Sie prüft die Audio-URL und erneut die Ruhezeiten und übergibt die Nachricht an Notify. Erfolgreiche Übergabe garantiert noch keine hörbare Wiedergabe am Echo.

## 6. Optionale Karten für andere Dashboards

Nur falls zusätzlich gewünscht, als JS-Module unter Einstellungen → Dashboards → Ressourcen registrieren:

- `/tablet_assist_for_alexa/assist.js`
- `/tablet_assist_for_alexa/keepalive.js`

```yaml
type: custom:tablet-assist-conversation-card
```
```yaml
type: custom:tablet-assist-bt-keepalive
```

Assist-Karte nutzt die zuletzt genutzte Pipeline, optional eine explizite Pipeline-ID mit `pipeline:`. Beide Karten folgen der HA-Oberflächensprache. Keepalive spielt nach manuellem Start eine lautlose Audioschleife auf diesem Gerät ab und greift nicht auf das Mikrofon zu. Geräteabhängige Wirkung; bei Störungen stoppen.

## Altinstallation / Migration

Der frühere manuelle Installer mit Control Center, Timer- und Benachrichtigungsvorlagen bleibt in `homeassistant/` verfügbar. Diese Vorlagen installiert der Marketplace nicht automatisch. Neue Automationen können die Durchsageaktion verwenden. Keine automatische Migration alter Jarvis-Konfigurationen, Pipelines, Erinnerungen oder Raumregeln. Bestehende Sprachdienste erst nach Umstellung ihrer Verbraucher entfernen. Die neue Integration besitzt eine eigene Domain und überschreibt die alten Komponenten nicht.

## Status

Marketplace-Struktur vorbereitet; vollständige Neuinstallation, HA-Laufzeit, GPU-Inferenz, Bluetooth und öffentliche HTTPS-Wiedergabe müssen praktisch geprüft werden. Entwicklungsvorschau, keine offizielle Zertifizierung oder bestätigte Aufnahme in den öffentlichen Katalog.
