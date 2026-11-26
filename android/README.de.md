# TAFA Device Bridge · Android 1.2.1

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Native Anbindung des Tablets an Home Assistant: Rufwort und Assist, Bluetooth-Ausgabe, Kamera und Bewegungserkennung – mit einer übersichtlichen Oberfläche. Android 9+.

**Erstinstallation:** Zuerst [TAFA in Home Assistant einrichten](../docs/setup-guide.md), dann für jedes Tablet einen eigenen Nicht-Admin-HA-Benutzer anlegen. In der Device Bridge die HA-Basisadresse und Zugangsdaten unter **Verbinden** hinterlegen. Die HA-App enthält keine Android-APK; die signierte Device Bridge wird separat installiert.

## Drei übersichtliche Tabs

**Status** zeigt die Verbindungen und Aktivitäten und bietet direkt **Verbinden**, **Jetzt sprechen**, **Rufwort starten**, **Gespräch beenden** und **Kamera starten**. Jetzt sprechen startet eine Frage ohne Rufwort; fehlende Zugangsdaten führen zu Verbinden, ein fehlendes Rufwort-Modell zu Einstellungen.

**Verbinden** wird einmal für den Test- oder Produktivserver eingerichtet: HA suchen, Basisadresse ohne Dashboard-Pfad eingeben, Token des eigenen HA-Raumnutzers einfügen oder scannen und die Verbindung speichern/starten. Für unverschlüsseltes lokales HTTP ist eine ausdrückliche Freigabe je Adresse nötig.

**Einstellungen** enthält sämtliche Bedienelemente: Player starten/stoppen, Android-Bluetooth-Kopplung, lautloses Echo-Keepalive, Rufwortmodell und Mikrofoneinstellungen, native Assist-Pause und Test, Display-Helligkeitsfreigabe, Kamera-Linse, Bildintervall, Bildbewegung, Kamera starten/stoppen, Hilfe und Diagnose. Die Feinabstimmung ist nicht mehr in einem versteckten Untermenü.

## Sprach- und Audioeinrichtung

1. Unter **Verbinden** den passenden HA-Server und das Token des dedizierten Nicht-Admin-Raumnutzers eingeben. Die TAFA-Integration muss auf diesem HA-Server eingerichtet sein.
2. Den Echo in den Android-Bluetooth-Einstellungen für Medienaudio koppeln.
3. Unter **Einstellungen → Echo & Audioplayer** den Player starten; optional das lautlose Bluetooth-Keepalive aktivieren.
4. Unter **Einstellungen → Rufwort** das lokale Vosk-Modell installieren, Rufwort wählen, Mikrofonberechtigung erteilen und die Erkennung starten. Die Sprache wird über die native HA-Assist-Pipeline übertragen.
5. Unter **Status** Verbindung und laufenden Sprachzustand prüfen.

Die App-ID `de.jarvis.audio`, verschlüsselte Zugangsdaten, Geräteschlüssel, gespeicherte Einstellungen und die Tablet-ID bleiben bei einem korrekt signierten Update erhalten. Die App nicht deinstallieren, wenn diese Daten erhalten bleiben sollen. Der Bildschirm kann über Android nur in der Helligkeit verändert, nicht zuverlässig vollständig ein- und ausgeschaltet werden.

## Mikrofonmodus in 1.2.1

Unter **Einstellungen → Native Sprachunterhaltung → Natives Mikrofon: Betriebsmodus** stehen **Stumm**, **Rufwort** und **Immer an** zur Wahl. Home Assistant speichert den Modus pro Tablet; erforderlich ist die TAFA-Integration **0.4.26 oder neuer**. Im Modus Immer an kann eine lokale Geräuschaktivität ohne Rufwort eine neue Anfrage auslösen. Die aktuelle Äußerung bleibt bis zum Sprechende nur im Arbeitsspeicher und wird danach vollständig an Assist übergeben. Während Erkennung und Bluetooth-Antwort pausiert der lokale Monitor. Für ein Rufwort vor jeder neuen Anfrage den Rufwortmodus ohne Folgefragen verwenden.

## Rufwort und Folgefragen

Unter **Einstellungen → Native Assist → Fragen ohne erneutes Rufwort** gilt standardmäßig **Rufwort für jede Frage**. Auch beim Update wird eine bisher unbegrenzte Unterhaltung nicht automatisch übernommen.

Optional lassen sich **1–10 zusätzliche Fragen pro Gespräch** erlauben. Beispiel: 1 bedeutet die erste Frage plus höchstens eine Folgefrage. Ein neues Rufwort oder Jetzt sprechen beginnt ein neues Gespräch. Stille, fehlende/fehlerhafte Antworten, Stummschalten oder das Limit beenden die Folgefragen. Gespräch beenden und Änderungen am lokalen Limit brechen auch eine vorgemerkte Aufnahme ab. Zum vollständigen Abschalten des Mikrofons den Rufwort-Dienst stoppen oder das Gerät in HA stummschalten.

Das lokale Limit ist eine feste Obergrenze unabhängig vom Dashboard. HA darf mit seinem Gerätewert followup_limit weniger erlauben (0 = keine, -1 = serverseitig unbegrenzt); HA kann das lokale Limit nicht erhöhen. Die App hatte diesen Wert bisher ignoriert. Die Browser-Steuerung berücksichtigt außerdem continue_conversation und beendet bei Stille. Die native Stilleerkennung basiert auf Audiopegeln: Während einer erlaubten Folgefrage können Geräusche weiterhin als Sprache fehlinterpretiert werden. Für laute Räume empfiehlt sich der Standard ohne Folgefragen.

## Kamera und Bewegung

Unter **Einstellungen → Kamera** Linse und Intervall (1/2/3/5/10 Sekunden) wählen. **Bildbewegung melden** aktiviert die einfache Erkennung von Pixeländerungen. Wenn der zugehörige TAFA-Raum in Home Assistant für Kamerabilder freigeschaltet ist und die Kamera auf dem Tablet ausdrücklich gestartet wurde, werden Bilder über die authentifizierte TAFA-Raumkamera-API übertragen. Home Assistant stellt pro Raum eine Kamera und einen Bewegungs-Binärsensor bereit. Der Sensor ist ohne frische Kamerabilder oder ohne aktivierte Bewegungserkennung nicht verfügbar. Die Bewegungserkennung erkennt keine Personen oder Gegenstände.

Die separate lokale Testvorschau wurde entfernt. Kameraaufnahmen erfolgen nur während des ausdrücklich gestarteten Vordergrunddienstes; es gibt keine dauerhafte Aufnahme oder Offline-Warteschlange. Die Kamera kann hier oder über ihre Benachrichtigung gestoppt werden. Bitte die Privatsphäre betroffener Personen beachten.

## Veröffentlichung und Installation

[Signierte APK 1.2.1 herunterladen](downloads/TAFA-Device-Bridge-1.2.1.apk) · [GitHub-Release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.2.1) · [SHA-256-Prüfsumme](downloads/SHA256SUMS). Die APK verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode **22**. Über die bestehende App installieren; Zugangsdaten und Gerätekennung bleiben erhalten.

Zum eigenen Bauen JDK 17, Android SDK Platform 35 und `build.ps1` verwenden; zum Signieren `sign-release.ps1` mit dem ursprünglichen Keystore. Private Schlüssel sind nicht im Repository enthalten. Die automatisierten Tests ersetzen keinen echten Bluetooth-/Mikrofontest.

[Versionshinweise](RELEASE_NOTES.de.md) · [Drittanbieterhinweise](THIRD_PARTY_NOTICES.de.md)
