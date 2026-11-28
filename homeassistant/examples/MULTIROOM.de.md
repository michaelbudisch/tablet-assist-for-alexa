# TAFA Multiroom – Tablets Home-Assistant-Räumen zuordnen

[English](MULTIROOM.md) · [Projekt](../../README.de.md) · [Gesamteinrichtung](../../docs/setup-guide.md)

**Aktueller Weg:** TAFA-App ab 0.4.65, Integration ab 0.5.3 und Device Bridge ab 1.3.1. Es werden **keine separaten TAFA-Räume im Control Center erstellt**: Die Home-Assistant-Bereiche sind maßgeblich.

## Einmalig pro Tablet

1. Unter **Home Assistant → Einstellungen → Bereiche, Labels & Zonen → Bereiche** den gewünschten Raum anlegen, falls er noch nicht existiert.
2. Für den nativen, getrennten Audio-/Kamerakanal benötigt derzeit jedes Tablet einen **eigenen aktiven Nicht-Admin-HA-Benutzer**. Das ist eine Zugriffsberechtigung, **keine zweite Raumzuordnung**. Das Token dieses Benutzers bleibt ausschließlich auf dem Tablet.
3. Die TAFA Device Bridge mit Home Assistant verbinden und den nativen Audioplayer starten. **Die App erzeugt und speichert selbst eine eindeutige 32-stellige Installationskennung.** Ein optionaler Gerätename in Android dient nur der Anzeige und weist keinen Raum zu.
4. Unter **Apps → TAFA → Benutzeroberfläche → Geräte & Multiroom** erscheint das Tablet **einmal** mit Kennung und Status. Im Feld **Home-Assistant-Raum** einen bereits vorhandenen HA-Bereich auswählen und **Raum zuweisen** drücken. TAFA richtet das interne Audiorouting automatisch ein und weist das Gerät im HA-Geräteregister dem Bereich zu. Kein manuelles Erstellen einer TAFA-Raum-ID und keine zweite Eigentümer-Zuordnung.
5. Rufwort und Sprachantwort auf diesem Tablet prüfen. Für einen Echo als Lautsprecher Android-Bluetooth-Medienaudio aktivieren.

Bei der **Neuinstallation** erhält die App eventuell eine neue Kennung. Wähle den gewünschten HA-Raum erneut aus; TAFA kann die alte, **offline** Installation desselben Benutzers ersetzen. Ein noch verbundenes anderes Tablet oder ein anderer Benutzer wird nicht automatisch verdrängt. Beim Wechsel in einen anderen Raum wird ausdrücklich bestätigt, da die vorherigen TAFA-Kameraentitäten dadurch entfallen können.

## Optionale Kamera und weitere Einstellungen

Unter **Geräte & Multiroom → Erweitert** lassen sich Kameraübertragung, native Geräteoptionen und Zurücksetzen aufrufen. Die Kamera ist bei einer neuen Raumzuordnung standardmäßig **aus**; aktiviere sie bewusst und starte die Kamera auf dem Tablet. Es werden nur aktuelle Einzelbilder vorgehalten. Ein Zurücksetzen des TAFA-Routings **löscht keinen Home-Assistant-Bereich und keinen HA-Benutzer**.

**Alexa-/Echo-Durchsageziele** unter **Funktionen & Datenquellen** sind eine unabhängige, optionale Zuordnung zu Home-Assistant-`notify`-Diensten. Sie stellen **keine Tablet-Räume** dar und ändern nicht die Gerätezuordnung.

## Fehlerbehebung

- **Tablet fehlt:** Prüfe die Android-Verbindung, das HA-Token und den gestarteten Audioplayer; jede App-Installation besitzt eine eigene Kennung.
- **„Raum nicht zuweisbar“:** Das Tablet darf nur unter seinem angemeldeten Nicht-Admin-Benutzer zugewiesen werden; ein bereits aktives fremdes Gerät wird nicht überschrieben.
- **Keine Sprachausgabe:** Rufwort, native Player-Verbindung und optional Android-Bluetooth prüfen. Ein grüner HTTP-Test beweist keine hörbare Ausgabe.
- **Ambient antwortet nicht:** Kontrolliere, ob dasselbe Tablet genau einem HA-Bereich zugeordnet ist, und lade die TAFA-Dashboard-Seite neu. Die visuelle Antwort bindet an die registrierte Gerätekennung.
- **Alte Jarvis-Karten/Automationen:** Nicht parallel neu installieren. Alte Kennungen in technischen Migrationsdateien sind kein weiterer laufender Assistent.

**Sicherheit:** Eine Installationskennung ist keine Authentifizierung. HA-Token nicht in Screenshots, Git oder Konfigurationsexporte aufnehmen und wenn möglich HTTPS verwenden.
