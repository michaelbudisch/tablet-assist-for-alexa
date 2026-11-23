# Jarvis · Tablet Assist for Alexa

[English](README.md) · **Deutsch**

**Dein lokaler KI-Sprachassistent für Home Assistant – mit Android-Tablet und Echo-Lautsprecher.**

![Developer Preview](https://img.shields.io/badge/Status-Developer%20Preview-orange) ![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-03a9f4) ![Local AI](https://img.shields.io/badge/AI-Lokal-0f766e)

Jarvis verbindet lokale Spracherkennung, Home-Assistant-Daten, optionale KI-Modelle und natürliche Sprachausgabe. Ein Android-Tablet dient als Mikrofon und Oberfläche; der Echo behält seine gewohnten Bluetooth- und Alexa-Funktionen.

## Funktionsübersicht

| Bereich | Funktionen |
|---|---|
| Sprache | Whisper STT, Rufwort, Gesprächsführung, Anschlussfragen |
| Audio | Piper als CPU-Basis, optional Qwen-Streaming, Echo Relay über Bluetooth |
| Haussteuerung | Lokale HA-Intents, Wetter, Energie, Heizung, Bring!, Abfall, Erinnerungen |
| KI | Optionales lokales Ollama-LLM, Modellwahl und Kontext-Einstellungen |
| Native Android-App | Echo Relay, Bluetooth-Streaming, Front-/Rückkamera, optionale Bildbewegungserkennung für HA |
| Vision | Lokale Einzelbildbeschreibung, Kameraansicht, optionale strukturierte Bewegungsauswertung |
| HA-Automationen | Wiederverwendbare Sprachausgabe mit Bestätigung, Wetterhinweise, Begrüßung, Testtimer |
| Familie | Drei optionale Namensfelder in HA-Helfern; keine Identitätserkennung |
| Durchsagen | Optionale Alexa-MP3-Durchsagen über temporäre HTTPS-Links |

**In der bestehenden privaten Hauszentrale getestet:** native Bluetooth-Sprachausgabe, HA-Sprechaktion, personalisierte Begrüßung und Testtimer. Die universelle Infobox ist dort eingerichtet; Ring-Ablauf und öffentliche neue Karte benötigen noch einen vollständigen End-to-End-Test.

> **Entwicklungsvorschau:** Basisintegration 0.3.1, Backend 1.6.0, GPU Worker 1.9.0 (aktualisiertes Schema), APK 0.5.0. Optionale Karte 1.3.0 und Automationsvorlagen sind noch kein vollständig geprüfter Neuinstallations-Release. Keine GPU für die CPU-Basis erforderlich.

## Neu: Native HA-Automationen

[Einrichtung der Automationsvorlagen und Familienfelder](docs/ha-automations.md). Das Dashboard bearbeitet die Namen, Home Assistant verwaltet Bedingungen, Wetter und Zeitfenster. Vision-Kategorien sind unsichere visuelle Schätzungen, keine Gesichtserkennung oder Identitätsfeststellung. Automatische Bildauswertung nur mit Zustimmung aller Betroffenen aktivieren.

## Architektur

```mermaid
flowchart LR
  A[Android tablet: native Assist] --> B[Home Assistant STT router]
  B --> C[CPU: Wyoming Faster Whisper]
  B -. optional .-> D[GPU: Wyoming STT]
  B --> E[Conversation router]
  E --> F[Local HA intents]
  E -. optional .-> G[Local LLM]
  E --> H[Streaming TTS with DSP]
  H --> I[CPU: Piper]
  H -. optional .-> J[GPU: Qwen TTS]
  H --> K[Android audio]
  K -->|Bluetooth| O[Echo speaker]
  E --> M[MP3 announcement API]
  M --> N[Temporary HTTPS MP3]
  N -->|optional Alexa notify| O
```

## Home Assistant Marketplace

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=michaelbudisch&repository=tablet-assist-for-alexa&category=integration)

**Home Assistant 2026.11+:** Einstellungen → Marketplace → Über Link hinzufügen → `https://github.com/michaelbudisch/tablet-assist-for-alexa` → Integration. Anschließend Tablet Assist for Alexa über den Integrationsdialog konfigurieren. Die Sprachserver werden separat installiert. [Einrichtung](docs/marketplace.md). Englische Bedienoberfläche und Dokumentation sind enthalten; Sprachbefehle und Modelle der enthaltenen Pipeline sind weiterhin deutsch.

Die native Assist-Integration bündelt STT, TTS und Gesprächsrouter ohne manuelle YAML-Bearbeitung. Der optionale Nginx-Proxy stellt ausschließlich kurzlebige MP3-Dateien bereit. Timer und Benachrichtigungsmanager des bisherigen Dashboards bleiben als manuelle Vorlagen erhalten; sie werden nicht durch den Marketplace installiert. Entwickler-Vorschau: keine vollständige Neuinstallation bestätigt.

## Native Android-App: Audio, Kamera und Bewegung

**[HA Jarvis Echo Relay 0.5.0](android/README.de.md)** bietet einen deutschen/englischen Android-Player mit HA-Suche, einmaligem Token-QR-Scan, bestätigter Bluetooth-Ausgabe und optionalem nativem Silent-Keepalive. [Fertige Vorschau-APK](android/downloads/HA-Jarvis-Echo-Relay-0.5.0-preview.apk). Die eigenständige [Echo Relay Assist Lovelace-Karte](docs/echo-relay-dashboard.md) verbindet die App ohne Hauszentrale mit einem beliebigen HA-Dashboard. Die Befehls-/Statushelfer werden separat eingerichtet; die Marketplace-Integration tut dies nicht automatisch.

Die App ist nicht nur ein Audioplayer: Sie kann ein Android-Smartphone oder Tablet als zusätzliche Kamera für Home Assistant bereitstellen. Die vorhandene Front- oder Rückkamera liefert nach ausdrücklicher Freigabe regelmäßig aktualisierte Einzelbilder. HA erhält eine Kamera-Entität und optional einen Bildbewegungssensor. Der lokale Vision-Worker kann für freigegebene Sichtfragen und HA-Automationen eingesetzt werden. Die Kamera-Funktion ist unabhängig von der Audiowiedergabe und muss bewusst gestartet werden; sie startet nicht automatisch nach einem Geräte-Neustart. Die Bilder werden nicht archiviert. Es handelt sich um Einzelbilder, nicht um einen vollwertigen Video-Livestream. [Details zur Android-App](android/README.de.md#kamera-und-lokales-visionmodell).

## Installation

```bash
git clone https://github.com/michaelbudisch/tablet-assist-for-alexa.git
cd tablet-assist-for-alexa
```

1. [Proxmox / Debian Sprachserver](docs/proxmox.md) — CPU-Basis und optionale LXC-Erstellung.
2. [Marketplace-Installation](docs/marketplace.md) — neue Integration empfohlen; oder [manuelle Legacy-Installation](docs/home-assistant.md) — Integrationen, Pipeline, Dashboard, Tablet-/Echo-Kopplung.
3. [Optional: Windows oder Linux KI-Rechner](docs/worker.md) — Faster Whisper, Qwen-TTS, Streaming, Ollama.
4. [Optionaler Nginx-Proxy-CT](docs/nginx-proxy.md) — nur für Alexa-MP3-Durchsagen; DuckDNS-App, Certbot und vorhandene Nginx-Proxy-CTs werden beschrieben.
5. [Sicherheit und Datenschutz](docs/security.md) — LAN-Zugriff, Bluetooth und Alexa-Ausgabe.
6. [Tests und Releasehinweise](docs/release.md).

Die Skripte sind für **Neuinstallationen**, nicht für die Migration einer bestehenden Jarvis-Installation. Keine produktive Konfiguration überschreiben. Eigene Hosts, Gerätezuordnungen und Schlüssel ausschließlich lokal konfigurieren.

## Lizenz

MIT für eigenen Projektcode; siehe [LICENSE](LICENSE). Abhängigkeiten und Modelle werden separat bezogen und unterliegen ihren jeweiligen Lizenzen: [Piper](https://github.com/OHF-Voice/piper1-gpl), [Wyoming Faster Whisper](https://github.com/OHF-Voice/wyoming-faster-whisper), [Home Assistant](https://www.home-assistant.io/), [Faster Qwen3 TTS](https://github.com/andimarafioti/faster-qwen3-tts), [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), [FFmpeg](https://ffmpeg.org/), [Ollama](https://ollama.com/). Modelle und Stimmen sind nicht enthalten. Lizenzbedingungen und Modellkarten vor der Verwendung prüfen. Unabhängiges Community-Projekt; keine Verbindung zu oder Unterstützung durch Amazon. Alexa und Echo sind Marken ihrer jeweiligen Eigentümer.
