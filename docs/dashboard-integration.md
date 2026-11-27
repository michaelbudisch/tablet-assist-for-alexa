# Entwicklerschnittstelle: TAFA mit einem eigenen Dashboard nutzen

[English](en/dashboard-integration.md) · [Control Center](control-center.md) · [Sprachsteuerung/Mikrofon](dashboard-voice-control.md) · [Multiroom](../homeassistant/examples/MULTIROOM.de.md)

Diese Anleitung richtet sich an Entwickler, die **nur TAFA als Sprach-KI verwenden** und ihre eigene Oberfläche in Home Assistant bauen möchten. TAFA braucht **kein** mitgeliefertes Lovelace- oder Ambient-Dashboard. Der native Sprachweg funktioniert weiterhin unabhängig davon, ob irgendeine Dashboard-Seite offen ist.

> **Stand:** Aktuelle TAFA-Integration mit den WebSocket-Befehlen `visual_identity` und `visual_subscribe`. Das sind relativ neue Schnittstellen. Änderungen und Erweiterungen sollten auf Abwärtskompatibilität geprüft werden.

## 1. Trennung von Logik und Darstellung

- **TAFA / Control Center**: Konfiguration von Whisper, Ollama/Qwen, TTS, Gesprächsagent, Datenquellen, Geräten und Räumen.
- **Android Device Bridge**: Rufwort, Spracheingabe, native HA-Assist-Verbindung und Bluetooth-/Tablet-Audio.
- **Dein Dashboard**: Entscheidet, **ob**, **wann** und **wie lange** Antworten visualisiert werden. Darstellung, Bilder, Animationen und Schaltflächen bleiben deine eigene Implementierung.
- **Private Jarvis-Ansicht / TAFA Dashboard DEV**: Beispiele und Entwicklungsoberflächen, **keine erforderliche API-Abhängigkeit**.

Nicht für eine zusätzliche KI-Anfrage den Text nochmals an Ollama schicken: **Verwende das von TAFA bereits erzeugte Antwort-Ereignis.**

## 2. Gerät und Raum eindeutig identifizieren

Ein Dashboard verwendet **nicht automatisch** das einzig vorhandene Tablet. Das ist besonders auf einem PC wichtig, der als Administrator angemeldet ist und alle Entitätszustände sehen kann.

Die bereits authentifizierte Home-Assistant-Verbindung eines Custom Elements bereitstellen:

```javascript
const result = await hass.callWS({
  type: "tablet_assist_for_alexa/visual_identity",
});
console.log(result.devices); // Nur Geräte, die das aktuelle HA-Konto sehen darf
```

Schematisches Ergebnis, **keine realen IDs**:

```json
{
  "devices": [{
    "device_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "room": "buero",
    "label": "Büro",
    "user_id": "ha_room_user_id",
    "sensors": {
      "status": "sensor.tafa_beispiel_rufwortstatus",
      "mic": "sensor.tafa_beispiel_mikrofonstatus",
      "last": "sensor.tafa_beispiel_letztes_rufwort"
    }
  }]
}
```

- `device_id` ist die **32-stellige Device-Bridge-ID**, nicht die ID aus dem HA-Geräteregister.
- `room` ist die für Audio gekoppelte Raumkennung. `label` kann abweichend benannt sein. **Nicht** allein nach dem sichtbaren Raumtitel routen.
- `user_id` bezeichnet den dem Raum zugeordneten HA-Benutzer.
- Die drei `sensors` liefern die tatsächlichen Entitäts-IDs, auch nach Umbenennungen.
- Nicht-Admins erhalten nur Geräte, die dem eigenen Raumnutzer zugeordnet sind; Admins können alle sehen.
- Eine leere Liste bedeutet: keine berechtigte Raumzuordnung verfügbar; dann **nicht** irgendeinen fremden Rufwortsensor verwenden.

**Lokale Auswahl:** Speichere für jede Browser-/WebView-Installation bewusst eine `device_id` oder die Einstellung **„Kein Sprachgerät“**. Ein Desktop ohne zugeordnetes Gerät bleibt passiv. Ein Android-Tablet darf nur bei eindeutiger und nachvollziehbarer Kopplung automatisch vorausgewählt werden.

## 3. Antworten abonnieren, nicht nachfragen

Der WebSocket-Ereignisstrom sendet fertige Gesprächsantworten. Er braucht keine zusätzlichen Mikrofonrechte und keinen zweiten KI-Aufruf.

```javascript
// hass: authentifiziertes Home-Assistant-Objekt deines Custom Elements
// selectedDeviceId: vom Nutzer für DIESES Display gewählte Geräte-ID
async function subscribeTafaInfobox(hass, selectedDeviceId, showCard) {
  const {devices} = await hass.callWS({
    type: "tablet_assist_for_alexa/visual_identity",
  });
  const local = devices.find(d => d.device_id === selectedDeviceId);
  if (!local) return () => {}; // Passives Display: nichts abonnieren

  return hass.connection.subscribeMessage((packet) => {
    const data = packet?.event?.data || packet?.event || packet?.data || packet;
    // Nicht nach Benutzer allein filtern: Admin-PC und Tablet können
    // unterschiedliche oder auch dieselbe HA-Anmeldung verwenden.
    if (data?.tafa_device_id !== local.device_id) return;
    if (data?.user_id !== local.user_id) return;
    if (typeof data.reply !== "string" || !data.reply.trim()) return;

    showCard({
      title: data.topic === "knowledge" ? "Wissen"
           : data.topic === "weather" ? "Wetter" : "TAFA",
      question: data.question || "",
      text: data.reply,
      topic: data.topic || "knowledge",
    });
  }, {
    type: "tablet_assist_for_alexa/visual_subscribe",
  });
}

// Bei disconnectedCallback() bzw. wenn das Gerät wechselt:
// const unsubscribe = await subscribeTafaInfobox(...);
// unsubscribe?.();
```

**Wichtig:** `hass.connection.subscribeMessage` gibt ein Promise auf die Abmeldefunktion zurück. Pro aktivem Display nur **ein** Abonnement führen und es beim Entfernen des Custom Elements, Verbindungswechsel oder Gerätewechsel auflösen. Eine Wissensfrage wie „Wer war Albert Einstein?“ ist **keine** eigenständige HA-Automatisierung.

### Nutzdaten

`visual_subscribe` übermittelt im Wesentlichen:

| Feld | Bedeutung |
| --- | --- |
| `question` | Erkannte Frage/Text, soweit vom Assist-Aufruf bereitgestellt |
| `reply` | Generierte Textantwort; UI entscheidet über den Zuschnitt |
| `topic` | Klassifikation, zum Beispiel `knowledge`, `weather` oder `search` |
| `user_id` | HA-Benutzerkontext der Sprachanfrage |
| `device_id` | Ursprüngliche HA-Assist-Geräte-ID: **nicht** als eindeutige TAFA-Kopplung interpretieren |
| `tafa_device_id` | Vom TAFA-Server aus einer **eindeutigen** Raumzuordnung ermittelte native Geräte-ID; kann bei mehrdeutiger Herkunft leer sein |
| `sources` | Optionales Mapping verfügbarer HA-Datenquellen; kein Ersatz für normale HA-Berechtigungsprüfungen |
| `results`, `selected_index`, `article` | Je nach Internetsuche gegebenenfalls zusätzliche Metadaten |

**Sicherheitsregel:** Bei leerem oder abweichendem `tafa_device_id` **keine** Raum-Infobox automatisch einblenden. Nicht auf „zuletzt aktives Gerät“ oder eine übereinstimmende Admin-Benutzer-ID ausweichen. Die serverseitige Berechtigungskontrolle beschränkt Nicht-Admin-Abonnements auf den eigenen HA-Raumnutzer; eine UI muss zusätzlich die konkrete lokale Gerätebindung prüfen.

## 4. Sprachzustände für eigene Animationen

Verwende die mit `visual_identity` zurückgegebenen Entitäten:

```javascript
const wake = hass.states[local.sensors.status]?.state || "";
const mic  = hass.states[local.sensors.mic]?.state || "";

let phase = "idle";
if (/^native_(?:speaking|playing|buffering|waiting_for_playback)/.test(wake)
    || /^(?:speaking|playing|tts)$/i.test(mic)) phase = "speaking";
else if (/^native_(?:processing|thinking|transcribing|sending_audio)/.test(wake))
    phase = "processing";
else if (/^(?:detected|native_(?:listening|connected|followup))/.test(wake))
    phase = "listening";
```

Diese Statusmuster sind **Beispiele** für ein Frontend, keine Garantie sämtlicher zukünftiger Zustände. Insbesondere `listening: hey_jarvis` beschreibt meist den dauerhaft scharfgeschalteten **Rufwort-Standby** und darf nicht als aktive Spracheingabe dargestellt werden.

## 5. Eigene Infoboxen und Einstellungen

Eine eigene Infobox ist **keine** Funktion des Control Centers. Lege selbst fest:

- Anzeigedauer (z. B. 30 Sekunden), Position und ob mehrere Meldungen eine Warteschlange bilden;
- Titel, Text, Bilder und optionale Quellen;
- Animation und Verhalten beim Wechsel zwischen Idle, Zuhören, Verarbeiten und Ausgabe;
- Rückkehr zur vorherigen Dashboard-Ansicht.

Eine Wetter-Infobox und eine Wissens-Infobox können unterschiedliche Vorlagen verwenden, sollen aber denselben **gerätegebundenen Antwortstrom** benutzen. Wikipedia-Bilder müssen optional, datenschutzbewusst und vom Dashboard selbst geladen werden; TAFA garantiert keine automatische Bildlieferung zu jeder Frage.

Für **proaktive** Infoboxen aus HA-Automatisierungen kann eine eigene Dashboard-Integration zusätzliche Ereignisse auswerten. Das historisch privat verwendete `jarvis_infobox_show` ist **kein erforderliches TAFA-Kern-API**; es sollte nicht als einzige Integrationsmöglichkeit für neue Nutzer dokumentiert oder vorausgesetzt werden.

## 6. Mikrofon steuern

Für einfache Buttons **HA-Standardentitäten** benutzen: Mikrofon-Stummschaltung, nativer Sprachmodus und Anschlussfragen. Beispiele und Admin-WebSocket-Befehle stehen unter [TAFA-Sprachsteuerung](dashboard-voice-control.md). Die Infobox-Subscription selbst ist **nur lesend** und steuert kein Mikrofon.

## 7. Fehlersuche mit zwei Displays

1. Auf **PC und Tablet** `visual_identity` auslesen. Admins sehen eventuell mehr Geräte als normale Raumnutzer.
2. Das Tablet auf seine **Device-Bridge-ID** binden; den PC auf **„Kein Sprachgerät“** setzen.
3. „Wer war Albert Einstein?“ und „Wie wird das Wetter?“ **am Tablet** fragen. Beide Antwortarten müssen denselben `tafa_device_id` tragen.
4. Nur das Tablet darf die Antwort anzeigen und auf seine Statussensoren reagieren. Der PC darf zwar andere HA-Werte anzeigen, aber keine fremde Sprachantwort.
5. Fehlt `tafa_device_id` trotz korrekt gekoppelter Räume, die Zuordnung unter **Control Center → Geräte & Multiroom** prüfen; keine Zuordnung aus dem Anzeigenamen erraten.
6. Bei verbundenem Bluetooth und fehlender Audioausgabe den nativen Player prüfen, **nicht** das Infobox-CSS.

**Versionierung:** Dokumentation und Beispiele gehören in Git; sie dürfen keine privaten Entitäten, Zugangsdaten, Tokens oder persönlichen Raum-IDs enthalten. Nutzer-Dashboards und bestehende HA-Automationen bei TAFA-Updates nicht ungefragt überschreiben.
