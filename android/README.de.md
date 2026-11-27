# TAFA Device Bridge · Android 1.2.9

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

**1.2.9:** Optionaler eigener HA-Sensor für Annäherung über die lokale Frontkamera. Mindestgesichtsgröße und Ausschaltverzögerung sind einstellbar. Enthält den aktuellen Git-Stand 1.2.8 mit lokal beendeten stillen Folgefragen. Mit bisheriger Signatur über die vorhandene App installieren.

Native Anbindung des Tablets an Home Assistant: Rufwort und Assist, Bluetooth-Ausgabe, Kamera und Bewegungserkennung – mit einer übersichtlichen Oberfläche. Android 9+.

**Erstinstallation:** Zuerst [TAFA in Home Assistant einrichten](../docs/setup-guide.md), dann für jedes Tablet einen eigenen Nicht-Admin-HA-Benutzer anlegen. In der Device Bridge die HA-Basisadresse und Zugangsdaten unter **Verbinden** hinterlegen. Die HA-App enthält keine Android-APK; die signierte Device Bridge wird separat installiert.

## Native Ablaufdiagnose

Unter **Einstellungen → Hilfe & Diagnose → Nativer Sprachablauf** findest du die letzten 20 nativen Anfragen: Sprachende-Latenz, Zeitachse, getrennte P50-/P95-Auswertung und lokalen JSON-Export ausschließlich mit Zeitmetadaten. [Anleitung zur Zeitmessung](docs/native-flow-diagnostics.de.md).

## Drei übersichtliche Tabs

**Status** zeigt die Verbindungen und Aktivitäten und bietet direkt **Verbinden**, **Jetzt sprechen**, **Rufwort starten**, **Gespräch beenden** und **Kamera starten**. Jetzt sprechen startet eine Frage ohne Rufwort; fehlende Zugangsdaten führen zu Verbinden, ein fehlendes Rufwort-Modell zu Einstellungen.

**Verbinden** wird einmal für den Test- oder Produktivserver eingerichtet: HA suchen, Basisadresse ohne Dashboard-Pfad eingeben, Token des eigenen HA-Raumnutzers einfügen oder scannen und die Verbindung speichern/starten. Für unverschlüsseltes lokales HTTP ist eine ausdrückliche Freigabe je Adresse nötig.

**Einstellungen** bündelt die Bedienelemente in **Audio**, **Sprache & Rufwort**, **Raum & Gerät**, **Erweiterte Spracherkennung**, **Display & Kamera** und **Hilfe & Diagnose**. Antippen öffnet eine Gruppe; es bleibt jeweils nur eine geöffnet.

## Audioausgabe in 1.2.4

**Automatik** bevorzugt ein verbundenes Bluetooth-Mediengerät und verwendet ansonsten den Tablet-Lautsprecher. **Nur Bluetooth** bleibt ohne Bluetooth-Ausgang stumm; **Nur Tablet** nutzt den internen Lautsprecher. Bei einem Wechsel der Route wird die laufende Antwort gestoppt und die nächste Antwort wählt den aktuellen Ausgang. Die Auswahl ist auch pro Tablet im TAFA Control Center mit Integration **0.4.40** verfügbar. Echte Bluetooth- und Tablet-Audiotests bleiben erforderlich.

## Sprach- und Audioeinrichtung

1. Unter **Verbinden** den passenden HA-Server und das Token des dedizierten Nicht-Admin-Raumnutzers eingeben. Die TAFA-Integration muss auf diesem HA-Server eingerichtet sein.
2. Für Bluetooth-Ausgabe den Echo oder einen anderen Medienlautsprecher in den Android-Einstellungen koppeln. Der Tablet-Lautsprecher ist ebenfalls möglich.
3. Unter **Einstellungen → Audio** Automatik, Nur Bluetooth oder Nur Tablet wählen und den Player starten. Das lautlose Keepalive ist optional und gilt für Bluetooth.
4. Unter **Einstellungen → Sprache & Rufwort** das lokale Vosk-Modell installieren, Rufwort wählen, Mikrofonberechtigung erteilen und die Erkennung starten. Die Sprache wird über die native HA-Assist-Pipeline übertragen.
5. Unter **Status** Verbindung und laufenden Sprachzustand prüfen.

Die App-ID `de.jarvis.audio`, verschlüsselte Zugangsdaten, Geräteschlüssel, gespeicherte Einstellungen und die Tablet-ID bleiben bei einem korrekt signierten Update erhalten. Die App nicht deinstallieren, wenn diese Daten erhalten bleiben sollen. Der Bildschirm kann über Android nur in der Helligkeit verändert, nicht zuverlässig vollständig ein- und ausgeschaltet werden.

## Mikrofonmodus in 1.2.2

Unter **Einstellungen → Sprache & Rufwort → Natives Mikrofon: Betriebsmodus** stehen **Stumm**, **Rufwort** und **Immer an** zur Wahl. Home Assistant speichert den Modus pro Tablet; erforderlich ist die TAFA-Integration **0.4.26 oder neuer**. Im Modus Immer an kann eine lokale Geräuschaktivität ohne Rufwort eine neue Anfrage auslösen. Die aktuelle Äußerung bleibt bis zum Sprechende nur im Arbeitsspeicher und wird danach vollständig an Assist übergeben. Während Erkennung und Bluetooth-Antwort pausiert der lokale Monitor. Für ein Rufwort vor jeder neuen Anfrage den Rufwortmodus ohne Folgefragen verwenden.

## Direkte HA-Steuerung in 1.2.3

Mit TAFA-Integration **0.4.28** werden Mikrofon- und Gesprächseinstellungen über den authentifizierten Geräte-WebSocket direkt übernommen. Ohne Push-Verbindung gleicht die App den Zustand per REST ab. Der Wechsel vom Modus Immer an zum Rufwortmodus lädt das Offline-Modell bei Bedarf.

Das Control Center kann nach Bestätigung einer Einstellung die gemessene Steuerungs-Rundlaufzeit anzeigen. Die App meldet außerdem den aktiven Steuerungskanal und ihre lokale Obergrenze für Folgefragen. Reale Umschaltzeiten müssen auf dem Tablet geprüft werden.

## Rufwort und Folgefragen

Unter **Einstellungen → Sprache & Rufwort → Fragen ohne erneutes Rufwort** gilt standardmäßig **Rufwort für jede Frage**. Neue Installationen starten ohne Folgefragen; ein bereits gewähltes Limit bleibt erhalten.

Optional lassen sich **1–100 zusätzliche Fragen pro Gespräch oder ausdrücklich unbegrenzt** erlauben. Beispiel: 1 bedeutet die erste Frage plus höchstens eine Folgefrage. Ein neues Rufwort oder Jetzt sprechen beginnt ein neues Gespräch. Stille, fehlende/fehlerhafte Antworten, Stummschalten oder das Limit beenden die Folgefragen. Gespräch beenden und Änderungen am lokalen Limit brechen auch eine vorgemerkte Aufnahme ab. Zum vollständigen Abschalten des Mikrofons den Rufwort-Dienst stoppen oder das Gerät in HA stummschalten.

Das lokale Limit ist eine feste Obergrenze unabhängig vom Dashboard. HA darf mit seinem Gerätewert followup_limit weniger erlauben (0 = keine, -1 = serverseitig unbegrenzt); HA kann das lokale Limit nicht erhöhen. Die App hatte diesen Wert bisher ignoriert. Die Browser-Steuerung berücksichtigt außerdem continue_conversation und beendet bei Stille. Die native Stilleerkennung basiert auf Audiopegeln: Während einer erlaubten Folgefrage können Geräusche weiterhin als Sprache fehlinterpretiert werden. Für laute Räume empfiehlt sich der Standard ohne Folgefragen.

## Kamera und Bewegung

Unter **Einstellungen → Display & Kamera** Linse und Intervall (1/2/3/5/10 Sekunden) wählen. **Bildbewegung melden** aktiviert die einfache Erkennung von Pixeländerungen. Wenn der zugehörige TAFA-Raum in Home Assistant für Kamerabilder freigeschaltet ist und die Kamera auf dem Tablet ausdrücklich gestartet wurde, werden Bilder über die authentifizierte TAFA-Raumkamera-API übertragen. Home Assistant stellt pro Raum eine Kamera und einen Bewegungs-Binärsensor bereit. Der Sensor ist ohne frische Kamerabilder oder ohne aktivierte Bewegungserkennung nicht verfügbar. Die Bewegungserkennung erkennt keine Personen oder Gegenstände.

Die separate lokale Testvorschau wurde entfernt. Kameraaufnahmen erfolgen nur während des ausdrücklich gestarteten Vordergrunddienstes; es gibt keine dauerhafte Aufnahme oder Offline-Warteschlange. Die Kamera kann hier oder über ihre Benachrichtigung gestoppt werden. Bitte die Privatsphäre betroffener Personen beachten.

## Veröffentlichung und Installation

[Signierte APK 1.2.9 herunterladen](downloads/TAFA-Device-Bridge-1.2.9.apk) · [GitHub-Release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.2.9) · [SHA-256-Prüfsumme](downloads/SHA256SUMS). Die APK verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode **30**. Über die bestehende App installieren; Zugangsdaten und Gerätekennung bleiben erhalten.

Zum eigenen Bauen JDK 17, Android SDK Platform 35 und `build.ps1` verwenden; zum Signieren `sign-release.ps1` mit dem ursprünglichen Keystore. Private Schlüssel sind nicht im Repository enthalten. Die automatisierten Tests ersetzen keinen echten Bluetooth-/Mikrofontest.

[Versionshinweise](RELEASE_NOTES.de.md) · [Drittanbieterhinweise](THIRD_PARTY_NOTICES.de.md)

## Annäherung am Tablet (Versuch)

Unter **Einstellungen → Display & Kamera → Annäherung** aktivieren, **Frontkamera** wählen und **Kamera starten**. Am üblichen Bedienabstand mit 25 % und 4 Sekunden beginnen; wird zu weit entfernte Anwesenheit erkannt, die Mindestgröße erhöhen. Die Live-Anzeige hilft beim Einstellen. Das ist eine Näherung aus der Gesichtsgröße, keine Meterangabe. Bildbewegung und Begrüßungen sind unabhängig. Kamera- und Mikrofonberechtigungen bleiben getrennt.

Der neue HA-Binärsensor **Annäherung** erscheint am registrierten TAFA-Tablet. Die neue Geräteschnittstelle wird mit der Integration ausgeliefert; vor dem App-Test HA aktualisieren und neu starten. Bei deaktivierter Kamera oder fehlenden Meldungen wird er nicht verfügbar. Bereits laufende Bildübertragung verwendet weiter ihr eigenes Intervall. Das Kameramodell ist Teil der APK; kein GPU Worker erforderlich.
