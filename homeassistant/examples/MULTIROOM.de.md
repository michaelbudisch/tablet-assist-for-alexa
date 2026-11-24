# Jarvis Multiroom – experimentelle Version 0.1

[English](MULTIROOM.md)

## Voraussetzungen und Grenzen

Multiroom benutzt denselben zentralen Home Assistant, GPU-Worker und CPU-Fallback wie bisher. Es wird kein zusätzlicher Worker installiert. Der bisherige Einzelgeräte-Modus bleibt verfügbar. Dieser Entwicklungsstand ist kein veröffentlichter APK-Release und nicht auf einem produktiven HA getestet.

Pro Raum genau ein dediziertes, aktives Nicht-Admin-HA-Konto, ein Tablet mit Relay-App und optional ein lokal per Bluetooth verbundener Echo. Im Raum-Dashboard dasselbe dedizierte Konto verwenden. Die Raumzuordnung wird serverseitig aus dem authentifizierten HA-Konto abgeleitet. Keine gemeinsamen Raumkonten; keine Admin-Tokens in der Relay-App. Verwende den bestehenden vertrauenswürdigen HA-HTTPS-Zugang. Die Zugriffsrechte auf andere Home-Assistant-Ressourcen werden weiterhin von HA bestimmt; das Routing ersetzt kein HA-Berechtigungssystem.

## Einrichtung (erst auf einer Testinstallation)

1. Den vollständigen Integrationsordner des Entwicklungsbranches installieren, nicht das ältere Ring-Overlay; HA neu starten. Bestehende Integration und Einstellungen vorher sichern.
2. In HA zwei separate Nicht-Admin-Benutzer anlegen. Auf dem ersten Tablet einen Raum-Benutzer anmelden; den zweiten Benutzer ausschließlich für den zweiten Raum verwenden.
3. Die Dateien `jarvis-room-admin-v0.1.0.js` und `jarvis-room-assist-v0.1.0.js` aus `homeassistant/www/jarvis/` nach `/config/www/jarvis/` kopieren. Unter Einstellungen > Dashboards > Ressourcen als JavaScript-Modul hinzufügen:
   - `/local/jarvis/jarvis-room-admin-v0.1.0.js`
   - `/local/jarvis/jarvis-room-assist-v0.1.0.js`
4. Auf einem Administrator-Dashboard eine manuelle Karte mit `type: custom:jarvis-room-admin` hinzufügen. Räume (z. B. `wohnzimmer` und `buero`) und je einen Benutzer auswählen. Optional die HA-Geräte-ID eines dem jeweiligen Bereich zugeordneten Geräts hinterlegen. Die beiden Ruhezeitfelder leer lassen, wenn keine Ruhezeit gewünscht ist. Die Karte bietet Status, Konfiguration, Entkoppeln und Durchsagen an ausdrücklich ausgewählte Räume.
5. Die aus dem Android-CI gebaute Test-APK installieren. Pro Tablet den vorhandenen HA-Zugang mit Token des zugeordneten Raumkontos konfigurieren und **Raum-Audio (experimentell)** aktivieren. Echo lokal über Bluetooth koppeln, Player starten. Bei nicht erreichbarem Player gibt es keinen Rückfall auf fremde Räume.
6. Auf einem separaten Dashboard für jeden Raum (angemeldet mit dessen Konto) die manuelle Karte einfügen:
   ```yaml
   type: custom:jarvis-room-assist-card
   pipeline_id: DEINE_ASSIST_PIPELINE_ID
   instance_id: wohnzimmer
   ```
   Instance-ID pro Raum eindeutig halten. Die Karte verwendet die bestehende Assist-Pipeline und den lokalen Android-Audiostream. Gesprächskontext verbleibt in der jeweiligen Karteninstanz; die vom Administrator konfigurierte HA-Geräte-ID wird an Assist übergeben. Raumspezifische Befehle wie „Mach das Licht an“ hängen von der korrekten Geräte-/Bereichszuordnung und dem HA-Agenten ab. Testen, bevor man sich darauf verlässt.

## Gezielte Durchsage

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

Alternativ `room: wohnzimmer` für einen Raum. Nur explizit ausgewählte Räume werden angesprochen. Automatische Durchsagen berücksichtigen Ruhezeiten und gemeldete Auslastung; bewusste Fragen sind weiterhin möglich. `accepted` bedeutet angenommen, nicht abgespielt. Die Raumkarte verfolgt den bestätigten Android-Wiedergabestatus eigener Antworten.

## Optionale Begrüßung

`multiroom-greeting.example.yaml` ist ein standardmäßig deaktiviertes Beispiel für einen bestehenden lokalen Bewegungssensor. Raumname, Sensor, Zeiten und Text anpassen. Es gibt keine neuen Kameras, keine Identitätserkennung und keine raumübergreifende Personenverfolgung. Keine Innenraumkamera muss für Multiroom aktiviert werden. Die vorhandene Einzelgeräte-Kamera-Begrüßung wird nicht automatisch migriert. Die Beispiel-Begrüßung setzt ihren Tagesmarker nach Annahme des Audioauftrags; eine spätere Wiedergabe ist damit nicht garantiert. Automatische Durchsagen können ausfallen, wenn ein Dashboard gerade das Mikrofon nutzt (auch Wakeword-Betrieb).

## Testmatrix vor Freigabe

- Zwei getrennte Benutzer: jeweils eigene Antwort; kein Audioauftrag in anderem Raum.
- Zwei gleichzeitig gestellte Fragen: keine gegenseitige Überschreibung; Worker-Wartezeiten messen.
- Android-Player stoppen, neu starten, Bluetooth trennen: keine Weiterleitung an andere Räume.
- Gezielt mehrere Räume auswählen; Ruhezeiten, beschäftigten Player und aktive Mikrofonaufnahme berücksichtigen.
- Eindeutige HA-Geräte-ID und Bereich prüfen; lokale Steuerung pro Raum testen.
- Bestehenden Einzelgerätebetrieb, Piper-Fallback und laufende Ring-/Tablet-Automationen nach einem späteren Upgrade erneut prüfen.
- Android-CI und echte HA-Integrationstests müssen erfolgreich sein; ein echter Test mit zwei Tablets/Echos bleibt erforderlich.

Keine Änderung an der privaten Hauszentrale, am GPU-Worker oder an laufenden HA-Entitäten.
