# TAFA Multiroom – mehrere Tablets einrichten

[English](MULTIROOM.md) · [Projekt](../../README.de.md) · [Gesamteinrichtung](../../docs/setup-guide.md)

**Aktueller Weg für Neuinstallationen:** Multiroom ist Teil der einheitlichen TAFA-Integration und **TAFA Device Bridge 1.2.1**. Die alten separaten Jarvis-Komponenten, Legacy-Helfer, manuellen Lovelace-Karten und APKs 0.x sind **nicht notwendig**. [Ältere Multiroom-Dokumentation](archive/legacy-MULTIROOM.de.md) ist nur für Migrationen gedacht.

## Voraussetzungen

- [TAFA-App und TAFA Lokal](../../docs/setup-guide.md) sind eingerichtet; Piper/Whisper stehen lokal in TAFA oder extern zur Verfügung.
- Je Tablet ist die [signierte TAFA Device Bridge](../../android/README.de.md) installiert; Android 9+ und Berechtigung für Mikrofon und Audio.
- Für jeden Raum ist **ein eigener aktiver HA-Benutzer ohne Administratorrechte** vorhanden. Einen Benutzer/Token nicht gleichzeitig für mehrere Räume verwenden.
- Optional je Tablet ein per **Android-Bluetooth** gekoppelter Echo-Medienlautsprecher; der Echo bleibt weiterhin normal als Alexa-Gerät nutzbar.

## Raum und Gerät koppeln

1. In HA einen **eigenen Nicht-Admin-Benutzer** für das Tablet anlegen; die Zugangsdaten geschützt aufbewahren.
2. Unter **TAFA → Geräte & Multiroom** den Raum erstellen beziehungsweise auswählen und den zugehörigen Benutzer hinterlegen. Eine neue Raumkennung kann vor der Tablet-Registrierung angelegt werden; **keine Vier-Geräte-Grenze**.
3. In Device Bridge unter **Verbinden** die HA-Basisadresse ohne Dashboard-Pfad und den **Token genau dieses Raumnutzers** eintragen. Im Tab **Rufwort** das lokale Modell aktivieren beziehungsweise die Erkennung starten, damit sich das Gerät registriert.
4. In **TAFA → Geräte & Multiroom** das registrierte Tablet auswählen, dem Raum/Benutzer zuordnen und **Audio-Raum verbinden**. Eine Übertragung zwischen bereits zugeordneten Benutzern ausdrücklich bestätigen.
5. Auf dem Tablet **Multiroom-Audio** und den **Player** einschalten. In TAFA die Zustände **verbunden**, **Player bereit** und **letzter Kontakt** prüfen.
6. Einen kurzen Sprachtest auf genau diesem Tablet durchführen. Für Echo-Ausgabe muss dessen Bluetooth-Medienaudio auf dem **jeweiligen Tablet** aktiv sein.

Ein registriertes Rufwort-Gerät ist **noch kein** verbundenes Audio-Raumgerät. Bei „Player offline“ den nativen Player/Netzwerk und bei „Wiedergabe nicht bereit“ den Android-Medienausgang prüfen. Die Voice-Pipeline muss die TAFA-Streaming-TTS-Entität verwenden. Der Browser-Test **Jetzt sprechen** im Control Center spielt **im Browser** und beweist nicht automatisch Raum-Audio.

## Optionale Kamera und Geräteeinstellungen

Unter **Geräte & Multiroom → Tablet-Kameras je Raum** bewusst freigeben (Standard **Aus**) und erst danach auf dem Tablet Kamera starten. Der **Nicht-Admin-Raumbenutzer** genügt; keine Administrator-Tokens für die Kamera verwenden. Frische JPEG-Einzelbilder und grobe Bildbewegung sind keine kontinuierliche Videoaufnahme und keine Personenerkennung. Weitere Details: [Kamera-Anleitung](../../android/docs/camera-preparation.de.md).

Stumm/Rufwort/Immer an, Mikrofoneinstellungen und Geräteinformationen sind in TAFA beziehungsweise Device Bridge verfügbar. Aktivierte Kameras/Mikrofone mit anderen Haushaltsmitgliedern abstimmen. Jede HA-Anmeldung kann unterschiedliche Berechtigungen haben; Nicht-Admin bedeutet keine generelle Isolation sämtlicher HA-Entitäten.

## Fehlerbehebung und bestehende Installationen

- **Gerät fehlt:** In Device Bridge Verbindung, Raumnutzer und Rufwortdienst prüfen.
- **Keine Antwort am Echo:** Bluetooth-Medienausgang auf dem Tablet sowie Player und **Tablet Assist Stream** prüfen.
- **Whisper langsam/nicht verfügbar:** Unter **TAFA → Verbindungen** CPU-/GPU-Wyoming prüfen; die CPU-Rückfallebene ist unabhängig von Multiroom.
- **Alte Jarvis-Raumkarten oder Automationen:** Nicht parallel zu TAFA neu installieren. Die vorhandene HA-Konfiguration sichern, bevor alte Komponenten manuell migriert oder entfernt werden.

**Sicherheit:** HA-Token nicht in YAML/Git/Screenshots veröffentlichen. Lokales HTTP überträgt Zugangsdaten unverschlüsselt; vertrauenswürdiges HTTPS bevorzugen. Die Kamera startet nicht allein durch die Raumfreigabe.
