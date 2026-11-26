# Alte Echo-Relay-Lovelace-Karten (nur Migration)

[English](en/echo-relay-dashboard.md) · [TAFA neu einrichten](setup-guide.md) · [Aktuelles Multiroom](../homeassistant/examples/MULTIROOM.de.md)

**Nicht für neue TAFA-Installationen:** Die früheren Jarvis-/Echo-Relay-Karten, manuellen `input_text`-Helfer, `jarvis_tablet_audio`-Dienste und zusätzlichen JavaScript-Ressourcen werden für die einheitliche TAFA-Integration nicht benötigt.

Neuer Weg: Die signierte [TAFA Device Bridge](../android/README.de.md) mit Home Assistant verbinden, die **TAFA Lokal**-Pipeline prüfen und Tablets unter **TAFA → Geräte & Multiroom** verwalten. Die normale Sprachantwort wird vom nativen Android-Player über Bluetooth ausgegeben; **TAFA → Jetzt sprechen** dient nur dem Browser-Test.

Wer noch ein altes Jarvis-Dashboard migriert, findet den ursprünglichen Stand im [Archiv](archive/legacy-echo-relay-dashboard.de.md). Vor einer Migration Home Assistant sichern und bestehende Automatisierungen nicht ungeprüft ersetzen.
