# TAFA-Sprachsteuerung in eigenen Home-Assistant-Dashboards

[English](en/dashboard-voice-control.md) · [Nativer Sprachweg](native-only.md) · [TAFA-App](app.md) · [Entwickler: Antworten/Infoboxen](dashboard-integration.md)

Mit TAFA Device Bridge kann ein Home-Assistant-Dashboard das Mikrofon eines registrierten Tablets steuern – unabhängig davon, ob die native Android-App oder das Dashboard im Vordergrund angezeigt wird. **Die Haupt-README ist keine technische API-Anleitung**; diese Seite beschreibt die dafür vorgesehenen Schnittstellen.

## Am einfachsten: die normalen Home-Assistant-Entitäten

Ab der TAFA-Integration stehen pro Tablet unter **Einstellungen → Geräte & Dienste → TAFA → Geräte → Tablet** Entitäten bereit:

| Typ | Bedeutung | Benutzung |
| --- | --- | --- |
| `switch.…_mikrofon_stumm` | Stummschaltung des nativen Mikrofons | `switch.turn_on` = stumm, `switch.turn_off` = aktiv |
| `select.…_nativer_sprachmodus` | Art der Spracheingabe | `Rufwort` oder `Immer an` |
| `select.…_anschlussfragen_ha_grenze` | Obergrenze für Anschlussfragen | `Aus`, Zahl oder `App-Einstellung` |

Die konkreten **Entitäts-IDs hängen vom Tablet-Namen** ab. Die angezeigten IDs daher im eigenen HA ablesen und nicht aus Beispielen übernehmen.

Für eine einfache Lovelace-Karte reichen die Standard-Entitäten:

```yaml
type: entities
title: TAFA – Sprachsteuerung
entities:
  - entity: switch.tafa_beispieltablet_mikrofon_stumm
    name: Mikrofon stumm
  - entity: select.tafa_beispieltablet_nativer_sprachmodus
    name: Sprachmodus
  - entity: select.tafa_beispieltablet_anschlussfragen_ha_grenze
    name: Anschlussfragen
```

**Reihenfolge:** Zum Aktivieren zuerst den gewünschten Sprachmodus wählen und dann die Stummschaltung ausschalten. `Immer an` erkennt auch Gespräche in der Umgebung.

## Direkt über die Home-Assistant-WebSocket-API

Die in Home Assistant integrierte API läuft unter **`/api/websocket`**. Ein eigenes HA-Custom-Element nutzt die bereits authentifizierte HA-Verbindung (`hass.callWS`) und darf **keinen Zugangstoken in HTML, YAML oder JavaScript hinterlegen**.

**Schreibbefehl (nur für HA-Administratoren):**

```json
{
  "id": 41,
  "type": "tablet_assist_for_alexa/device_admin",
  "action": "configure",
  "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "settings": {"muted": false, "voice_mode": "wake"}
}
```

`device_id` ist die **32-stellige ID der registrierten Android-Installation**, nicht die HA-Geräte-ID. Sie lässt sich über den Befehl `tablet_assist_for_alexa/device_admin` mit `action:"list"` abfragen (Admin). Der Server validiert jede Änderung und speichert sie für dieses Tablet.

Die drei Schaltzustände werden **atomar** über dieselbe Schnittstelle gesetzt:

| Gewünschter Zustand | `settings` |
| --- | --- |
| **Stumm** | `{"muted":true}` |
| **Rufwort** | `{"muted":false,"voice_mode":"wake"}` |
| **Immer an** | `{"muted":false,"voice_mode":"continuous"}` |

Das Stummschalten bewahrt den zuvor ausgewählten Modus. Zum Ändern der HA-Grenze für Anschlussfragen: `{"followup_limit":5}` oder `{"followup_limit":-1}` für **keine zusätzliche HA-Grenze**.

In einem bestehenden, authentifizierten HA-Custom-Dashboard:

```javascript
async function setTafaMicrophone(hass, deviceId, mode) {
  if (!["mute", "wake", "continuous"].includes(mode)) {
    throw new Error("Invalid TAFA microphone mode");
  }
  const settings = mode === "mute"
    ? { muted: true }
    : { muted: false, voice_mode: mode };
  return hass.callWS({
    type: "tablet_assist_for_alexa/device_admin",
    action: "configure",
    device_id: deviceId,
    settings,
  });
}
```

`hass.callWS` setzt die vorhandene Home-Assistant-Anmeldung voraus; mit einem Nicht-Admin-Benutzer liefert der direkte Schreibbefehl einen Berechtigungsfehler. Wer ein Dashboard für normale Benutzer bauen möchte, sollte **die HA-Entitäten und deren Dienste** verwenden statt eines privilegierten Rohbefehls.

## Status-Updates per WebSocket abonnieren

TAFA Device Bridge **1.2.2+** empfängt Änderungen über:

```json
{
  "id": 42,
  "type": "tablet_assist_for_alexa/device_settings_subscribe",
  "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Dieser Befehl ist **nur lesend** und ist nur für die Person, der die Installation gehört, oder einen HA-Administrator erlaubt. Nach dem `result`-Paket `{"subscribed":true}` kommen `event`-Pakete mit dem aktuellen Zustand sowie jeder Konfigurationsänderung. Die Android-App selbst nutzt diese Ereignisse, damit kein dauernder HTTP-Abgleich erforderlich ist.

Beispiel für ein Ereignis ab der neuen Diagnoseversion:

```json
{
  "id": 42,
  "type": "event",
  "event": {
    "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "revision": 7,
    "muted": false,
    "voice_mode": "wake",
    "followup_limit": -1,
    "word": "Hey Jarvis"
  }
}
```

Weitere Felder können enthalten sein; maßgeblich ist das aktuelle Geräteobjekt. **`revision`** ist eine pro HA-Laufzeit vergebene Änderungsnummer, keine über Neustarts garantierte globale Nummer. Der Client muss damit keinen eigenen Authentifizierungsmechanismus erfinden.

## Verbindungsstatus und Laufzeitdiagnose

Im TAFA Control Center → **Jetzt sprechen** werden nach Aktualisierung beider Komponenten angezeigt:

- **Steuerkanal:** `WebSocket`, `500-ms-Abgleich` oder `nicht aktiv`.
- **Bestätigung:** Der Befehl wurde vom Tablet bestätigt oder steht noch aus.
- **Umschaltzeit:** Zeit vom Speichern der Einstellung in HA bis zur bestätigten Übernahme durch Android **inklusive Rückantwort über die Geräte-API**. Dies ist keine reine WebSocket-Einweglaufzeit und auch keine Messung von Whisper, KI oder Bluetooth.
- **Letzte Übernahme:** Zeitpunkt der letzten Android-Bestätigung.

Der native Android-Dienst benötigt für diese zusätzliche Bestätigung **Device Bridge 1.2.3+**. Mit älteren Apps bleiben diese Diagnosewerte nicht verfügbar, während die bisherige Mikrofonsteuerung weiterhin funktioniert.

### Anschlussfragen richtig einstellen

In der Android-App ausdrücklich `Unbegrenzt (bis Gesprächspause)` wählen, wenn längere Unterhaltungen ohne erneutes Rufwort erwünscht sind. Die HA-Option `App-Einstellung` (`followup_limit=-1`) bedeutet **kein zusätzliches HA-Limit**, *nicht*, dass die App ihre eigene Schutzgrenze ignoriert. Andere HA-Grenzen können die App-Einstellung nur einschränken. Stille, Fehler und Stumm beenden die offene Folgefrage; anschließend gilt wieder der gewählte Grundmodus. **Unbegrenzt bedeutet keine dauerhafte Speicherung von Gesprächen**.

### Sicherheit und Fehlersuche

- HA-Adminrechte sind nur für `device_admin` nötig; die normale HA-Entitätssteuerung folgt den jeweiligen HA-Berechtigungen.
- Nicht in eine öffentliche Webanwendung einbetten; keinen langfristigen HA-Token im Dashboard-Quellcode speichern.
- Bei `unauthorized` Geräte-ID, Gerätezuordnung und HA-Berechtigungen prüfen.
- Nach HA-Neustart verbindet die Device Bridge den WebSocket neu. Bei Verbindungsverlust prüft sie die Steuerung als Absicherung etwa alle **500 ms** per authentifizierter Geräte-API; Netzwerkzeiten können die tatsächliche Verzögerung erhöhen.
- `revision`, Latenzen und Bestätigungen werden als flüchtige Diagnosewerte behandelt; sie ersetzen nicht die aktuelle Einstellung in den HA-Entitäten.
