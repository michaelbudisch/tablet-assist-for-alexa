# TAFA Device Bridge · Android 1.1.0

[English](README.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Native Anbindung des Tablets an Home Assistant: Rufwort und Assist, Bluetooth-Ausgabe, Kamera und Bewegungserkennung – mit einer übersichtlichen Oberfläche. Android 9+.

## Drei übersichtliche Tabs

**Status** zeigt nur an, ob Home Assistant und der Bluetooth-Lautsprecher verbunden sind, was der Sprachassistent gerade tut, ob Rufworterkennung/Kamera/Keepalive laufen und wie voll der Akku ist.

**Verbinden** wird einmal für den Test- oder Produktivserver eingerichtet: HA suchen, Basisadresse ohne Dashboard-Pfad eingeben, Token des eigenen HA-Raumnutzers einfügen oder scannen und die Verbindung speichern/starten. Für unverschlüsseltes lokales HTTP ist eine ausdrückliche Freigabe je Adresse nötig.

**Einstellungen** enthält sämtliche Bedienelemente: Player starten/stoppen, Android-Bluetooth-Kopplung, lautloses Echo-Keepalive, Rufwortmodell und Mikrofoneinstellungen, native Assist-Pause und Test, Display-Helligkeitsfreigabe, Kamera-Linse, Bildintervall, Bildbewegung, Kamera starten/stoppen, Hilfe und Diagnose. Die Feinabstimmung ist nicht mehr in einem versteckten Untermenü.

## Sprach- und Audioeinrichtung

1. Unter **Verbinden** den passenden HA-Server und das Token des dedizierten Nicht-Admin-Raumnutzers eingeben. Die TAFA-Integration muss auf diesem HA-Server eingerichtet sein.
2. Den Echo in den Android-Bluetooth-Einstellungen für Medienaudio koppeln.
3. Unter **Einstellungen → Echo & Audioplayer** den Player starten; optional das lautlose Bluetooth-Keepalive aktivieren.
4. Unter **Einstellungen → Rufwort** das lokale Vosk-Modell installieren, Rufwort wählen, Mikrofonberechtigung erteilen und die Erkennung starten. Die Sprache wird über die native HA-Assist-Pipeline übertragen.
5. Unter **Status** Verbindung und laufenden Sprachzustand prüfen.

Die App-ID `de.jarvis.audio`, verschlüsselte Zugangsdaten, Geräteschlüssel, gespeicherte Einstellungen und die Tablet-ID bleiben bei einem korrekt signierten Update erhalten. Die App nicht deinstallieren, wenn diese Daten erhalten bleiben sollen. Der Bildschirm kann über Android nur in der Helligkeit verändert, nicht zuverlässig vollständig ein- und ausgeschaltet werden.

## Kamera und Bewegung

Unter **Einstellungen → Kamera** Linse und Intervall (1/2/3/5/10 Sekunden) wählen. **Bildbewegung melden** aktiviert die einfache Erkennung von Pixeländerungen. Wenn der zugehörige TAFA-Raum in Home Assistant für Kamerabilder freigeschaltet ist und die Kamera auf dem Tablet ausdrücklich gestartet wurde, werden Bilder über die authentifizierte TAFA-Raumkamera-API übertragen. Home Assistant stellt pro Raum eine Kamera und einen Bewegungs-Binärsensor bereit. Der Sensor ist ohne frische Kamerabilder oder ohne aktivierte Bewegungserkennung nicht verfügbar. Die Bewegungserkennung erkennt keine Personen oder Gegenstände.

Die separate lokale Testvorschau wurde entfernt. Kameraaufnahmen erfolgen nur während des ausdrücklich gestarteten Vordergrunddienstes; es gibt keine dauerhafte Aufnahme oder Offline-Warteschlange. Die Kamera kann hier oder über ihre Benachrichtigung gestoppt werden. Bitte die Privatsphäre betroffener Personen beachten.

## Veröffentlichung und Installation

[Signierte APK 1.1.0 herunterladen](downloads/TAFA-Device-Bridge-1.1.0.apk) · [GitHub-Release](https://github.com/michaelbudisch/tablet-assist-for-alexa/releases/tag/audio-v1.1.0) · [SHA-256-Prüfsumme](downloads/SHA256SUMS). Die APK verwendet die bisherige Signatur, App-ID de.jarvis.audio und Versionscode **20**. Über die bestehende App installieren; Zugangsdaten und Gerätekennung bleiben erhalten.

Zum eigenen Bauen JDK 17, Android SDK Platform 35 und `build.ps1` verwenden; zum Signieren `sign-release.ps1` mit dem ursprünglichen Keystore. Private Schlüssel sind nicht im Repository enthalten. Die automatisierten Tests ersetzen keinen echten Bluetooth-/Mikrofontest.

[Versionshinweise](RELEASE_NOTES.de.md) · [Drittanbieterhinweise](THIRD_PARTY_NOTICES.de.md)
