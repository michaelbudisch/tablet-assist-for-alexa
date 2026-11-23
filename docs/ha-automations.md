# Jarvis · Native Home-Assistant-Automationen (Vorschau)

[English](en/ha-automations.md) | **Deutsch** · [Projektübersicht](../README.de.md)

**Optional** · HA-Backend 1.6.0 mit aktualisierter Erkennungsvalidierung · GPU-Worker 1.9.0 mit erweitertem Vision-Schema · Echo Relay APK 0.5.0 · Lovelace-Karte 1.3.0.

## Einrichtung

1. Integration, Audiobrücke und Worker anhand der [regulären Anleitung](echo-relay-dashboard.md) installieren. Kamera und Bildbewegung nur mit Zustimmung aller Betroffenen aktivieren. Einzelbilder lokal halten, nicht archivieren und niemals zur Zugangskontrolle oder Identifizierung einsetzen.
2. Das [optionale Paket](../homeassistant/templates/echo-relay-automation-package.yaml) in ein bereits konfiguriertes HA-Paketverzeichnis übernehmen. **Keine vorhandenen Helfer oder Skripte doppelt anlegen.** Enthalten sind drei leere Namensfelder, Helfer für Sprechstatus und Sprachbridge, Zeitstempel der letzten Begrüßung, Fünf-Minuten-Timer, Sprechskript und deaktivierte Begrüßungsautomation. Den Zeitstempel vor dem ersten Test auf ein früheres Datum setzen. `weather.home` durch die eigene Wetter-Entität ersetzen. HA nach Installation von Paket und Integration neu starten.
3. Die fünf Module nach `/config/www/jarvis/` kopieren. Nur das Kartenmodul als Lovelace-Ressource registrieren und den alten Eintrag ersetzen. Dashboard vollständig neu laden. Diese Karte ist ein optionaler Vorschaupfad; Altinstaller und Vorlagen verwenden weiterhin die ursprüngliche Karte.
   - `echo-relay-assist-card-v1.3.0.js`
   - `jarvis-settings-v1.6.0.js`
   - `jarvis-proactive-v1.6.0.js`
   - `jarvis-model-settings-v1.1.0.js`
   - `jarvis-camera-preview-v1.2.0.js`
4. Vorhandene [Bewegungsautomation](../homeassistant/templates/echo-relay-proactive-automation.yaml) verwenden und die eigene Bewegungs-Entität einstellen. Über die Administrator-Aktion `jarvis_tablet_audio.proactive` (get/set) das vollständige Einstellungsobjekt übernehmen (ohne Revision, Status und Entitätslisten im Objekt settings). `enabled` und `test_mode` auf true, `greeting` auf false, `script_entity` leer lassen sowie `person` in `classes` auswählen. Das Backend begrenzt Prüfungen weiterhin durch Bildaktualität, Sperrzeit und Worker-Verfügbarkeit. Zeitfenster und Tagesgrenze regelt die HA-Automation. Die alte interne Begrüßung bleibt aus; Bewegungsautomation bei Nichtgebrauch deaktivieren.
5. Im Reiter **Familie** optionale Namen hinterlegen. HA speichert sie in Texthelfern; die Automation liest sie bei jeder Begrüßung. Kategorien sind fehleranfällige Schätzungen des sichtbaren Erscheinungsbilds, keine tatsächliche Geschlechts- oder Identitätsfeststellung. Bei mehreren oder unklaren Personen bleibt die Anrede neutral, unsichere Ergebnisse lösen kein Ereignis aus. Namen niemals zur Authentifizierung verwenden.
6. Bei sichtbarem Tablet-Dashboard und bereitem Echo Relay das Skript `script.jarvis_sprechen` zunächst mit kurzem Text und `followup: false` testen. Der Bereitschaftsstatus muss aktuell sein. `started` bestätigt den Wiedergabestart, nicht das Ende. Erst danach die Begrüßungsautomation aktivieren. Mit `timer.jarvis_begrussung_testfenster` ein fünfminütiges Testfenster starten; bei Erfolg endet es ohne Markierung des regulären Tages. Regulär: 06:00–10:00 Uhr, einmal täglich nach bestätigtem Wiedergabestart.

## Wiederverwendbare Aktionen

```yaml
action: script.jarvis_sprechen
data:
  message: "Die Waschmaschine ist fertig."
  followup: false
  daily_overview: false
response_variable: speech_result
```

Mögliche Statuswerte: `started`, `skipped`, `error`, `timeout`, `tablet_offline`, `tablet_busy`. Eine Rückfrage ist optional und erfordert ein sichtbares Dashboard; das Skript aktiviert keine dauerhafte Aufnahme. Für diese Vorschau ein fest zugeordnetes Tablet verwenden; die Koordination mehrerer Tablets ist für dieses Ereignis noch nicht getestet.

Die private Hauszentrale enthält zusätzlich die ereignisbasierte Infobox (`jarvis_infobox_show`) und ein deaktiviertes Ring-Beispiel. Diese kioskspezifischen Referenzfunktionen sind im Paket nicht enthalten. Die öffentliche Karte und eine vollständige Neuinstallation müssen noch auf echter Hardware getestet werden. Die bestehenden Sichtfragen und Kameravorschauen bleiben von der automatischen Begrüßung getrennt.
