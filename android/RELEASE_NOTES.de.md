# TAFA Device Bridge 1.0.1 (Quellcode-Kandidat — Signierung erforderlich)

- **Optionale native Sprachunterhaltung:** Reine Rufworterkennung bleibt Standard. Nach Aktivierung erkennt Vosk das Rufwort lokal; der Android-Vordergrunddienst streamt die Frage als 16-kHz-PCM zu Home Assistant Assist (Whisper → Gespräch → Qwen/Piper).
- Antworten über die vorhandene benutzergebundene Multiroom-Bluetooth-Verbindung, ohne geöffnetes Browser-Dashboard oder Browser-HTTPS. Bei LAN-HTTP gilt weiterhin die ausdrückliche Freigabe für unverschlüsselte Übertragung.
- Zwei optionale Anschlussfragen, einstellbare Sprechpause 900–3200 ms, manuelle Testtaste, Status und Stummschaltung.
- Gleiche App-ID und verschlüsselte Einstellungen, Versionscode 14. **Noch keine signierte kompatible APK, bis der private Original-Keystore verwendet wurde. Keine Umbenennung der signierten 1.0.0-APK!**
- Praktische Mikrofon- und Bluetooth-Tests am Tablet stehen noch aus.

---

# TAFA Device Bridge 1.0.0

Basis: Android 0.9.0, Quellstand 9cf27e7691a7340f98424ef044583f26528f2546.

- Neuer Name, freigegebenes Cyan-/Mint-Design, adaptives und monochromes App-Icon sowie Benachrichtigungssymbol.
- Vier Bereiche: Status, Verbinden, Rufwort und Hilfe. Gegliederte Kamera, aufklappbare Bluetooth-/Rufwort-Optionen und einheitliche Auswahlmenüs.
- Deutsche/englische Einrichtungshilfe. Bereich und aufgeklappte Optionen bleiben beim Sprachwechsel erhalten; ungespeicherte Token ausschließlich im Arbeitsspeicher.
- Dynamische Gerätekennung und gerätebezogene HA-Einstellungen aus 0.9.0 erhalten.

TAFA-Device-Bridge-1.0.0.apk über die vorhandene signierte App installieren. App-ID de.jarvis.audio, Signatur, Verschlüsselungsalias, Gerätekennung und Einstellungen bleiben erhalten; Versionscode 13.

Lokale Validierung: Build, JVM-Tests, Lint, Handy-/Tablet-UI und Signatur-/Paketprüfung. Physische Bluetooth- und Mehrtablet-Tests stehen aus. Passendes HA-Backend und TAFA-Dashboard bleiben erforderlich.
