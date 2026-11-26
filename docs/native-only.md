# TAFA: Ein Sprachweg, eine Benutzeroberfläche

**Ab TAFA-App 0.3.36 / HA-Integration 0.4.21 / Device Bridge 1.0.3**

## Architektur

Rufwort am Android-Tablet → native Mikrofonaufnahme → **Home Assistant Assist** mit der Pipeline **TAFA Lokal** (Whisper/Wyoming, Ollama und TTS) → TAFA-Raum-Audio-API → native Android-Wiedergabe über den gekoppelten **Bluetooth-Lautsprecher**. Es gibt keinen separaten Browser-Mikrofonmodus und keine konkurrierende Gesprächsübertragung. Qwen und Piper sind alternative *Stimmen beziehungsweise Backend-Dienste*, keine separaten Tablet-Audiowege.

Das alte zusätzliche **TAFA Dashboard** wird nicht mehr als Seitenleistenpanel registriert. Die Verwaltung befindet sich in **Home Assistant → Apps → TAFA → Benutzeroberfläche**. Vorhandene persönliche Dashboards, Automatisierungen und Assist-Pipelines werden nicht automatisch gelöscht oder umgeschrieben.

## Einrichtung

1. Installiere beziehungsweise aktualisiere die TAFA-App und starte Home Assistant Core nach der Aktualisierung des HA-Backends neu. Eine nicht von TAFA verwaltete HA-Integration überschreibt der Installer bewusst nicht.
2. Öffne TAFA → **Einrichtung** und verbinde Sprachserver, Wyoming-STT und den Ollama-Konversationsagenten. Im HA-Sprachassistenten muss eine funktionierende Pipeline **TAFA Lokal** ausgewählt beziehungsweise angelegt sein.
3. Installiere TAFA Device Bridge **1.0.3** auf dem Tablet. Verbinde die App mit Home Assistant über eine sichere HA-Anmeldung, erteile die Mikrofonberechtigung und starte den nativen Audio-Player sowie die Rufworterkennung.
4. Verbinde den gewünschten Echo- oder Bluetooth-Lautsprecher **in den Android-Bluetooth-Einstellungen** und prüfe normale Medienwiedergabe. Die App steuert den Hardware-Lautsprecher nicht über Alexa-Sprachbefehle.
5. Öffne TAFA → **Geräte & Multiroom**. Das gestartete Tablet registriert sich mit einer dauerhaften Geräte-ID. Stelle Rufwort, Stummschaltung und Mikrofonwerte direkt in HA ein. Änderungen werden regelmäßig von der App synchronisiert.
6. Für weitere Tablets verwendet jeder Audioraum einen **eigenen, nicht administrativen HA-Benutzer**. Melde das Tablet damit an und kopple Benutzer, Gerät und Raum unter **Geräte & Multiroom**. Die Zahl der Räume ist nicht fest auf vier begrenzt.

## Steuerung und Sensoren

Für jedes registrierte Tablet erstellt TAFA eigene HA-Entitäten:

- **Sensoren:** Sprachsteuerung online/offline, Wakeword-Status, Mikrofonstatus, Audioausgabe, Bluetooth, Akku, App-Version, letzter Kontakt und letztes Rufwort.
- **Schalter:** Mikrofon stumm, Display hell/gedimmt, optionale Displaysteuerung aktivieren.
- **Zahlenwerte:** Rufwort-Bestätigung und -Sperrzeit, Haltezeit, Sprechpause in Millisekunden, digitale Mikrofonverstärkung und Helligkeit.
- **Auswahl:** Wakeword (Hey Jarvis, Jarvis, Alexa oder alle drei).

Du kannst diese Entitäten in Home Assistant verwenden und die Einstellungen im TAFA Control Center ändern. Die App lädt sie periodisch erneut. Bei fehlender HA-Verbindung gibt die Rufworterkennung das Mikrofon aus Sicherheitsgründen frei, statt mit womöglich veralteten Stummschaltewerten weiterzulaufen.

**Folgefragen haben keine Anzahlgrenze.** Die nächste Aufnahme beginnt nach einer erfolgreichen Sprachantwort. Sie endet nach einer nicht beantworteten Aufnahme, manueller Stummschaltung oder Stopp; der Android-Mikrofondienst bleibt nutzergesteuert.

## Display und Android-Grenzen

Die spezielle Android-Berechtigung **„Systemeinstellungen ändern“** wird nur für eine optionale Helligkeitssteuerung benötigt. Sie muss auf jedem Tablet bewusst freigegeben und die Displaysteuerung zusätzlich in TAFA aktiviert werden. TAFA kann die Helligkeit dimmen und wieder erhöhen, aber **ohne privilegierte Geräteverwaltung das Display nicht zuverlässig physisch ausschalten, entsperren oder aus einem Tiefschlaf aufwecken**. Automatische Helligkeit und Hersteller-Energiesparfunktionen können das Verhalten beeinflussen.

## Updates und Datensicherheit

- Geräteeinstellungen und Namen liegen im authentifizierten HA-Speicher; die Android-App enthält keine fest kodierten Tabletslots.
- Weder Audioaufnahmen noch Sprachtranskripte werden in den Tablet-Telemetriesensoren gespeichert.
- Die native App benötigt für ein Update über eine bereits installierte Release-APK **denselben Android-Signaturschlüssel**. Eine CI-Debug-APK kann nicht einfach darüber installiert werden.
- Beim Wechsel von alten Jarvis-Routen die HA-Konfiguration und persönliche Dashboards sichern. Bestehende Automatisierungen bleiben unverändert; entferne veraltete Automatisierungen nur nach eigener Prüfung.
