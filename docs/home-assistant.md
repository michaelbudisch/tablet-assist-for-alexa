# Historische manuelle Jarvis-Installation

[English](en/home-assistant.md) · [Aktueller TAFA-Einrichtungsleitfaden](setup-guide.md) · [TAFA-App](app.md)

**Achtung: Diese Seite ist keine Neuinstallationsanleitung.** Der bisherige Weg mit zwei getrennten Jarvis-Integrationen, manuell kopierten Lovelace-Karten, selbst erstellten Helfern und tokenbasierten Piper-/GPU-APIs gehört zu älteren Versionen.

Für **neue TAFA-Installationen** wird die einheitliche TAFA-App (CPU-Dienste und Control Center) empfohlen; alternativ kann die Integration ohne App über [Marketplace](marketplace.md) installiert werden. **Nicht beide Installationswege parallel verwenden.**

Einzelne frühere Dienste und Automationen können in bestehenden Systemen noch verwendet werden. Vor einer Migration: HA sichern, eigene Dashboards, Helfer und Automatisierungen inventarisieren, dann gezielt auf [TAFA Lokal](setup-guide.md) mit STT-, Gesprächs- und TTS-Router umstellen. Ein altes `piper_api_token` oder der separate `jarvis_tablet_audio`-Backend-Installationsschritt gehört **nicht** zu einer frischen TAFA-Installation.

Die bisherige ausführliche Anleitung ist unter [Historische Jarvis-Installation](archive/legacy-home-assistant.de.md) nur für Nachschlagezwecke erhalten. Alte Befehle/URLs können überholt sein und dürfen nicht ungeprüft auf aktuellem HA ausgeführt werden.
