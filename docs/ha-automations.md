# Optionale Home-Assistant-Automationen mit TAFA

[English](en/ha-automations.md) · [Projekt](../README.de.md) · [Aktuelle Einrichtung](setup-guide.md)

**Für Neuinstallationen gilt:** Die TAFA-App richtet Sprachbackend und Dashboard ein. Sie übernimmt **keine** vorhandenen privaten Haushaltsautomationen, benennt sie nicht um und schaltet sie nicht automatisch ein. Automationen für Waschmaschine, Kameras, Begrüßungen, Ruhezeiten oder Alexa-Durchsagen benötigen **jeweils eigene HA-Entitäten und bewusste Freigaben**.

## Vorgehen

1. Zunächst [TAFA Lokal](setup-guide.md), Android Device Bridge und den gewünschten Raum-Audioplayer vollständig einrichten und eine echte Frage erfolgreich abspielen.
2. Für reine Bluetooth-Sprachantworten **keine öffentliche Alexa-MP3-Domain** einrichten. Für ausdrücklich gewünschte **Alexa-Notify-MP3-Durchsagen** erst [HTTPS-Audio/Proxy](proxmox.md) sowie den passenden HA-Alexa-Notify-Dienst prüfen.
3. Die tatsächlich vorhandenen HA-Sensor-/Ereignis-IDs und Raumzuordnungen vor einer neuen Automation kontrollieren. Keine generischen Beispiel-IDs blind übernehmen; nur eine Kopie in einer Testumgebung aktivieren.
4. Kamera- und Bewegungsdaten nur nach ausdrücklicher Freigabe nutzen. Ein Visionmodell kann Personen oder Gegenstände falsch beschreiben; Kamerahypothesen nicht als verlässlichen Identitäts- oder Zustellnachweis behandeln.
5. Automationen mit zeitlichem Auslöser, Ruhezeiten oder mehrfacher Benachrichtigung zunächst **deaktiviert** anlegen, gezielt testen und erst danach aktivieren. Doppelansagen vermeiden.

Die frühere Vorlage für **Jarvis Echo Relay 0.x** mit manuell angelegten `input_text`-Helfern, `jarvis_tablet_audio.proactive` und separater Lovelace-Karte gehört **nicht** zur neuen TAFA-Installation. Sie bleibt nur als [historische Referenz](archive/legacy-ha-automations.de.md) erhalten. Das Archiv ist kein ausführbares Erstinstallationsrezept.

**Sicherheit:** Keine Sprachaufnahmen, Tokens oder vertrauliche Nachrichten in öffentlich abrufbare MP3-/Log-Dateien schreiben. Vor Änderungen an vorhandenen HA-Automationen immer eine Sicherung erstellen.
