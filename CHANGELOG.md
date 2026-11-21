# Changelog

## 0.2.0 — Developer Preview
- Marketplace-kompatible Einzelintegration `tablet_assist_for_alexa` mit `hacs.json`, deutscher und englischer Einrichtung, STT- und TTS-Routing, Gesprächsmodus und optionaler Alexa-Ansageaktion.
- Verbindungsparameter und Klangprofile per Konfigurationsdialog statt Quellcode-Platzhaltern; optionale Assist-/Bluetooth-Karten enthalten.
- Separater unprivilegierter Nginx-Proxy-CT mit ACME/Certbot, begrenztem Audio-Pfad, Erneuerung und Installationsanleitung.
- Legacy-Installer und Timer-/Hinweisvorlagen bleiben erhalten. Keine automatische Migration; End-to-End-Test mit frischem Home Assistant und öffentlichem HTTPS ausstehend.

## 0.1.0 — Developer Preview
- Initiale öffentliche Projektstruktur unter Tablet Assist for Alexa.
- CPU-Sprachserver mit Piper, Faster Whisper, MP3-Klangprofilen und Cache; Proxmox-/Debian-Installationsskripte.
- Bereinigte HA-Integrationen mit Gesprächsrouter, Live-Klangprofilen, Erinnerungen, konfigurierbaren automatischen Hinweisen und Dashboard-Karten.
- Original-GPU-Worker v1.5.0 mit Windows-Setup; zusätzlich Linux-Setup, ohne private Konfiguration.
- MIT-Lizenz für eigenen Code, getrennte Drittanbieter-Lizenzen.
- Quellprüfungen und lokale Audio-Tests. Neuinstallation, GPU-Inferenz und Gerätekompatibilität müssen praktisch geprüft werden.
