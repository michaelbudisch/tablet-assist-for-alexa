# Jarvis Multiroom — HA-Backend 1.7.0 / Android 0.6.0

[English](MULTIROOM.md) | **Deutsch** · [Projekt](../../README.de.md)

Ein Home Assistant, mehrere Tablets und Bluetooth-Lautsprecher mit getrennten Audiokanälen sowie optionalen Kamera-/Bewegungsentitäten. Ein zentraler CPU-Sprachserver und optionaler GPU-Worker 2.2.0 reichen aus. Einzelgeräte-Modus bleibt verfügbar. Ein echtes Tablet mit Raum-Audio, Kamera und Dashboard-Ausgabe wurde erfolgreich getestet; automatisierte Zwei-Raum-HTTP-/Entitäts- und Routingtests sind enthalten. Gleichzeitiger Hardwaretest mit zwei Tablets und komplette Neuinstallation stehen aus.

## 1. Backend und Karten installieren

- HA sichern. Die vollständige [Jarvis Tablet Audio-Integration](../custom_components/jarvis_tablet_audio/) auf 1.7.0 in `/config/custom_components/jarvis_tablet_audio/` aktualisieren, Konfiguration erhalten, prüfen und HA neu starten. Bei Neuinstallation zuerst [HA-Grundeinrichtung](../../docs/home-assistant.md) und [CPU-Sprachserver](../../docs/proxmox.md) einrichten. Die Marketplace-Basisintegration installiert dieses separate Backend nicht automatisch.
- `jarvis-room-admin-v0.2.0.js` und `jarvis-room-assist-v0.1.1.js` aus [homeassistant/www/jarvis](../www/jarvis/) nach `/config/www/jarvis/` kopieren. Einstellungen → Dashboards → Ressourcen (gegebenenfalls erweiterter Modus): beide URLs `/local/jarvis/jarvis-room-admin-v0.2.0.js` und `/local/jarvis/jarvis-room-assist-v0.1.1.js` als JavaScript-Module registrieren. Ältere URLs derselben Karten ersetzen, Browser neu laden.
- Assist-Pipeline mit STT, Gesprächsagent und Jarvis-Streaming-TTS (z. B. `tts.jarvis_tablet_stream`) einrichten. Für optionales Rufwort zweite Pipeline mit kompatibler Wakeword-Erkennung konfigurieren. Eigene Pipeline-IDs in HA bzw. über die Assist-Pipeline-Listen-API ermitteln.

## 2. Pro Tablet ein Raumkonto erstellen

1. Einstellungen → Personen → Benutzer: je Tablet einen eigenen aktiven Benutzer **ohne Administratorrechte** anlegen, z. B. Jarvis Wohnzimmer. Starkes eigenes Passwort verwenden. Nur lokaler Zugriff ist sinnvoll, wenn vertrauenswürdiges lokales HTTPS funktioniert. Falls ein externer HTTPS-Hostname mit lokalem Konto die Anmeldung blockiert, bewusst über externen Zugriff entscheiden; keine Adminrechte für Multiroom vergeben.
2. Administrator-Dashboard anlegen und manuelle Karte hinzufügen:

   ```yaml
   type: custom:jarvis-room-admin
   ```
3. Raumkennung (z. B. `wohnzimmer`) eingeben, Benutzer wählen, Raum hinzufügen. HA legt Gerät, Kamera und Bewegungsentität an. Unter Einstellungen → Geräte & Dienste → Geräte dem Gerät den passenden HA-Bereich zuordnen. Geräte-ID aus URL der Geräteansicht in das optionale Feld HA-Geräte-ID der Raumverwaltung übernehmen und speichern. Assist erhält so Bereichskontext. Optional beide Ruhezeiten einstellen.
4. Für weitere Tablets wiederholen. Konten/Token nicht zwischen Räumen teilen. Routing erfolgt anhand des authentifizierten HA-Benutzers, nicht eines frei übermittelten Raumnamens. Normale HA-Entitätsberechtigungen gelten weiterhin; Nicht-Admin bedeutet keine vollständige Entitätsisolation.

## 3. Android-App einrichten

[Signierte APK 0.6.0](../../android/downloads/HA-Jarvis-Echo-Relay-0.6.0-preview.apk) über vorhandene Version installieren. Lokalen Echo über Android-Bluetooth koppeln und Medienwiedergabe testen. Als Raumbenutzer in HA anmelden, unter Profil → Sicherheit langlebigen Zugriffstoken erstellen, einmaligen QR-Code scannen oder Token privat in Relay eingeben. HA-Basisadresse eintragen, **Raum-Audio (experimentell)** aktivieren und Player starten bzw. neu starten.

App und Dashboard müssen **denselben Raumbenutzer** nutzen. Vertrauenswürdiges HTTPS bevorzugen. Die App kann nach ausdrücklicher Freigabe eine numerische lokale HTTP-Adresse nutzen (Token/Medien im LAN unverschlüsselt); das Browser-/WebView-Mikrofon benötigt dennoch vertrauenswürdiges HTTPS und Mikrofonberechtigung. Lokales HTTP funktioniert für Dashboard-Mikrofon nicht. Wenn bestehendes HTTPS funktioniert, sind keine Routeränderungen nötig. Keine Token in Git oder Dashboard-YAML.

**Optional für Offline-Nutzung:** [Lokales HTTPS / Split-DNS](../../docs/local-https.md) nutzt einen vorhandenen NGINX-/Certbot-Proxy und denselben sicheren Domainnamen im Heimnetz. Kein zweiter HA-Proxy nötig; lokales HTTP reicht für das Browser-/WebView-Mikrofon nicht.

## 4. Raum-Assistent im Dashboard

Normales, nicht auf Administratoren beschränktes Dashboard erstellen, manuelle Karte hinzufügen:

```yaml
type: custom:jarvis-room-assist-card
title: Jarvis · Raum-Assistent
pipeline_id: DEINE_JARVIS_PIPELINE_ID
# Optional: wake_pipeline_id: DEINE_WAKEWORD_PIPELINE_ID
instance_id: wohnzimmer
```

Je Raum eigene Instance-ID verwenden. Als Raumbenutzer auf dem Tablet anmelden, Karte öffnen. Sie soll Raumname und Echo Relay verbunden anzeigen. Mikrofon bzw. „Einmal sprechen“ in der Karte verwenden, nicht den nativen Assist-Knopf in der HA-Kopfzeile. Mikrofonberechtigung erteilen, Aufnahme bewusst starten, kurze Frage stellen und Antwort am zugehörigen Bluetooth-Echo prüfen. HA-Geräte-ID liefert Bereichskontext, sofern Pipeline/Agent dies unterstützen. Kein Rückfall auf fremde Räume, keine globalen Audiohelfer.

Eigene Dashboards benötigen eine ausdrückliche Umstellung des Transports. Der optionale [generische Kiosk-Audioadapter](../www/jarvis/jarvis-kiosk-room-audio-v0.1.0.js) ist nur für kompatible eigene Voice-Controller gedacht; Standardinstallationen verwenden die eigenständige Karte. Privates Kiosk-Layout und Konfiguration werden nicht veröffentlicht.

## 5. Optionale Kamera und Bildbewegung

Freigabe standardmäßig aus. Nur in gemeinsam genutzten Räumen mit informierter Zustimmung aller Anwesenden aktivieren, nicht in privaten Räumen. In Raumverwaltung Kamera erlauben, speichern, am Tablet ausgewählte Kamera ausdrücklich starten. Lokal oder über sichtbare Benachrichtigung stoppen. Entzug der HA-Freigabe löscht das Bild und weist weitere Uploads ab. 1/2/3/5/10 Sekunden Intervall wählen, tatsächliche Rate hängt von Aufnahme/Upload ab. Regelmäßig aktualisierte JPEGs, kein vollwertiges Video. Bilder verfallen nach 15 Sekunden im RAM, kein Archiv. Optionale grobe lokale Bildbewegung, keine Identitätserkennung oder raumübergreifende Personenverfolgung. Ausdrückliche Tablet-Sichtfragen des Raumkontos nutzen dessen eigene Kamera ohne Rückfall auf die Einzelkamera. HA-Kameraberechtigungen gelten. Android 0.6.0 kann bei fehlender Freigabe noch die alte Admin-Token-Meldung anzeigen; Freigabe/Konto prüfen, **keinen Admin-Token nutzen**.

## 6. Durchsagen

In HA Entwicklerwerkzeuge → Aktionen oder in einer Automation:

```yaml
action: jarvis_tablet_audio.room_audio
data:
  action: announce
  rooms:
    - wohnzimmer
    - buero
  message: "Das Essen ist fertig."
response_variable: result
```

Für einen Raum stattdessen `room: wohnzimmer`. Raumverwaltung bietet Durchsagen an ausgewählte Räume. Automatische Durchsagen beachten Ruhezeiten und gemeldete Auslastung; accepted bedeutet angenommen, nicht abgespielt. Optionales [deaktiviertes Begrüßungsbeispiel](multiroom-greeting.example.yaml) nutzt lokalen Bewegungssensor ohne Kamera/Identitätserkennung. Platzhalter/Tagesbegrenzung konfigurieren; Tagesmarker bei Annahme. Alte Automationen werden nicht automatisch migriert.

## Fehlerbehebung

| Problem | Prüfung |
|---|---|
| App verbunden, Karte nicht bereit | Gleiches Raumkonto; neue Karte/Ressource, Browser neu laden; Status-/HTTP-Fehler beachten. |
| Mikrofonfehler | Vertrauenswürdiges HTTPS, Mikrofonberechtigung, konkurrierende Mikrofonaufnahmen beenden. |
| Kamera verweigert / Admin-Token-Meldung | Raumfreigabe und Konto prüfen; lokal neu starten. |
| Keine Sprache | Bluetooth-Medienroute, laufender Player, Streaming-TTS, gezielte Testdurchsage. |
| Falscher Raum | HA-Bereich, Geräte-ID, Agent-Unterstützung. |
| Tablet umziehen | Kamera/Player stoppen, alte Zuordnung aufheben, neuen Raum/Konto konfigurieren, Bereich und Karten-Instance aktualisieren. |

Vor Einsatz mehrerer Tablets getrennte Antworten, gleichzeitige Anfragen, Offline-/Beschäftigt-Verhalten ohne fremden Rückfall, Kameras/Stopp und Ruhezeiten prüfen. [Android-Einrichtung](../../android/README.de.md) · [Sicherheit](../../docs/security.md).

## Personalisierte Begrüßung mit Büro-Kamera (Backend 1.7.1)

Der bisherige `proactive`-Dienst wertete nur den alten Echo-Relay-Kamerastream aus. Ab Backend 1.7.1 akzeptiert die Administratoraktion `jarvis_tablet_audio.proactive` mit `action: check` optional `room: buero` und prüft dann frische Bilder der ausdrücklich aktivierten Multiroom-Kamera. Der ausgewertete Raum wird im Ereignis `jarvis_echo_relay_detection` als `room` zusammen mit der `camera_entity_id` übermittelt.

Für bestehende Systeme die Dateien `relay_proactive.py` und `relay_camera.py` aus `homeassistant/custom_components/jarvis_tablet_audio/` in die entsprechende HA-Integration kopieren und die Integration neu laden oder HA neu starten. Der neue Dienstparameter ist **erst danach** verfügbar. Das Backend-Setting `greeting` bleibt aus, wenn bereits die HA-Raumautomation Audio ausgibt.

Im technischen Auslöser `automation.jarvis_tablet_bewegung_mit_vision` den Bewegungstrigger auf `binary_sensor.jarvis_tablet_buero_bildbewegung` setzen und der Aktion `jarvis_tablet_audio.proactive` neben `action: check` den Wert `room: buero` geben. Dann die allgemeine `automation.jarvis_morgendliche_begrussung_buro_multiroom` deaktivieren und die vorbereitete ereignisbasierte `automation.jarvis_buro_personalisierte_begrussung_multiroom` aktivieren.

Die Namen stammen aus `input_text.jarvis_name_mann`, `input_text.jarvis_name_frau` und `input_text.jarvis_name_kind`. Visuelle Kategorien sind unsichere Schätzungen und **keine verlässliche Identitätsfeststellung**. Nur bei eindeutiger Ein-Personen-Schätzung wird ein hinterlegter Name genutzt; andernfalls bleibt die Begrüßung neutral. Nicht zur Authentifizierung nutzen. Kamera nur mit informierter Zustimmung der Betroffenen aktivieren.

### TAFA-Kiosk: Raum-Audio auch bei später vergebenen Adminrechten

Die **eigenständige Jarvis-Raumkarte** nutzt den Raum-Audiodienst bereits korrekt. Ein separat integriertes TAFA-Dashboard kann dagegen anhand von `is_admin` fälschlich auf den alten Audio-Helfer wechseln. Der Helfer bleibt dann möglicherweise auf `idle`, obwohl der **zugewiesene Raumplayer online und bereit** ist.

Für eigene Kiosk-Integrationen gibt es die [wiederverwendbare Raum-Erkennung](../www/jarvis/tafa-room-routing-v0.1.0.mjs). Sie fragt den **angemeldeten** HA-Benutzer über `POST /api/jarvis_echo_relay/room_audio` (`action: status`) ab. Nur bei vorhandener Zuordnung wird der Raum-Ausgabeweg eingeschaltet; ohne Zuordnung bleibt der alte Audio-Pfad bestehen. Im Anschluss an die Erstellung der `Voice`-Instanz in `ensureVoice(card)`, **vor** der bisherigen `if(v.roomMode&&!v._roomAttached)`-Abfrage:

```js
const v = card._jarvisIntegratedVoice;
if (!v.roomMode && !v._tafaRoomProbeStarted) {
  import(new URL("/local/jarvis/tafa-room-routing-v0.1.0.mjs", location.origin).href)
    .then(m => m.maybeEnableProvisionedRoomAudio(card, v, ensureVoice))
    .catch(error => console.warn("TAFA room routing:", error));
}
// Bestehendes if(v.roomMode&&!v._roomAttached) unverändert lassen.
```

Dazu das Modul aus dem Git-Repository nach `/config/www/jarvis/` kopieren. Der private TAFA-Hauszentralen-Quellcode wird nicht öffentlich mitgeliefert; das Modul verändert deshalb ohne diese Einbindung kein bestehendes Dashboard. Für **neue Räume** weiterhin getrennte **Nicht-Admin-Benutzer** anlegen. Der funktionierende Raumplayer, seine Zuordnung und andere Räume werden nicht verändert. Tests: `node --test tests/test_tafa_room_routing.mjs`.
