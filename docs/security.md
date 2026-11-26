# Datenschutz und Sicherheit

[English](en/security.md) · [TAFA einrichten](setup-guide.md) · [Projekt](../README.de.md)

## Zugriffe und lokale Dienste

- Die **TAFA Device Bridge** verwendet die normalen **Home-Assistant-Anmelde-/Zugriffstokens**. Je Tablet ein eigenes aktives **Nicht-Admin-Konto** verwenden; Tokens nicht in Git, Screenshots, YAML oder öffentliche Logs übernehmen.
- Die **CPU-/GPU-Worker-APIs** für Piper, Wyoming Whisper, Qwen, Vision und Ollama sind im aktuellen neuen Installationsweg **ohne zusätzlichen TAFA-API-Token** erreichbar. Tokenfrei bedeutet **nicht öffentlich**: Die Ports **5000, 5001, 10300, 10502, 10503, 11434** und gegebenenfalls **8080/10501** ausschließlich im vertrauenswürdigen LAN halten und per Firewall auf benötigte Hosts begrenzen. **Keine Router-Portweiterleitungen** auf diese Dienste.
- Die **TAFA-App** erfordert eine autorisierte HA-Administratorsitzung für das Control Center. Der Windows-Worker-Export enthält private IP-Adressen und eine dauerhafte Gerätekennung, aber keine Passwörter; JSON/TXT und `.env` lokal behalten.
- **DuckDNS-Kontotokens** und HA-Zugriffstokens sind weiterhin echte Zugangsdaten und **nicht** dasselbe wie ein entfallener TAFA-Worker-API-Token.

## Mikrofon, Kamera und Testprotokoll

Die native Android-Aufnahme und ein aktiviertes Rufwort werden dem Gerät über einen sichtbaren Dienst/Berechtigungen gestattet. **Immer an** kann Hintergrundsprache erkennen; die Funktion nur mit informierter Zustimmung und angemessenen Geräteberechtigungen verwenden. Der Browserbereich **TAFA → Jetzt sprechen** kann nach ausdrücklicher Aktivierung bei sichtbarer Seite automatisch zuhören und zeigt ein vorübergehendes Gesprächsprotokoll an; es ist **kein dauerhaft gespeichertes Audioarchiv**. Die Speicher-/Protokolleinstellungen von Home Assistant und optionalen Drittanbietern separat prüfen.

Raumkameras starten erst nach **bewusster HA-Freigabe und Start auf dem Tablet**. Fotos und Visionergebnisse sind fehleranfällig und dürfen nicht zur Personenidentifizierung verwendet werden. Räume mit gemeinsam genutzten Mikrofonen oder Kameras entsprechend kennzeichnen.

## Alexa, HTTPS und Fernzugriff

Normale Antworten laufen **Tablet → Bluetooth → Echo** und benötigen keine öffentliche Audio-Domain. **Optionale Alexa-MP3-Durchsagen** nutzen Amazon-Dienste und einen öffentlich erreichbaren **HTTPS-Dateizugriff** für zufällig benannte, kurzlebige Audiodateien; keine vertraulichen Nachrichten über diesen Weg ausgeben. Ein öffentlicher Proxy darf **nur** die erforderliche Dateiroute anbieten, niemals Sprachgenerator-, Wyoming-, Vision- oder Ollama-APIs.

Lokales [HTTPS/Split-DNS](local-https.md) schützt die Browser-Mikrofonvoraussetzungen im LAN, **macht aber vorhandene öffentliche HA-Proxy-Routen nicht privat**. Öffentlichen HA-Zugriff mit sicheren Passwörtern, MFA und geprüften Regeln absichern; DNS-Port 53 nie ins Internet weiterleiten.

Eigene Automationen und Datenschutzeinstellungen werden bei TAFA-Updates nicht automatisch übernommen oder neu konfiguriert. Vor produktiven Kamera-/Sprach- oder Proxy-Änderungen eine HA-Sicherung und eine unabhängige Prüfung durchführen.
