# TAFA – Tests und Release-Checkliste

[English](en/release.md) · [Projekt](../README.de.md) · [Einrichtungsleitfaden](setup-guide.md)

**Versionsquellen statt veralteter fester Zahlen:** Die aktuelle **TAFA-App** steht in [`tafa_app/config.yaml`](../tafa_app/config.yaml), die **HA-Integration** in [`manifest.json`](../custom_components/tablet_assist_for_alexa/manifest.json), die **Device Bridge** in [`android/VERSION`](../android/VERSION) und der **GPU Worker** in [`worker/VERSION`](../worker/VERSION). Ein signiertes Android-Release kann sich vom Quellcode unterscheiden.

## Automatisierte Prüfungen

GitHub Actions prüft je nach Workflow u. a. Python/JavaScript-/Shell-Syntax, HA-Integrations- und Proxmox-Installertests, App-Installations-/Rollback-Logik, GPU-Worker-Skripte, Android-Build und Port-/Konfigurationsverträge. Für öffentlich verlinkte Anleitungen gibt es jetzt **`python tests/test_docs_public.py`** (relative Links, persönliche Standardwerte, wichtige Setup-Verträge) zusätzlich zu **`python tests/check_sources.py`**.

**Ein erfolgreicher CI-Build ist kein vollständiger physischer Erstinstallationstest.** Nach jedem Release die tatsächlichen Workflow-Ergebnisse für den jeweiligen Commit prüfen und Tests bei Änderungen der Installationsskripte erneut ausführen.

## Manuelle Erstinstallations-Checkliste

1. **Sauberes HA OS** ab 2026.11 auf der Zielarchitektur installieren, Backup machen, TAFA aus dem App-Repository hinzufügen. Anfangszustand: `speech_mode=setup`, **kein CPU-Modell-Download vor der bewussten Auswahl**.
2. **Lokal:** Piper/Faster-Whisper nach Auswahl `local` starten und eine echte Sprachfrage testen. **Extern:** Proxmox-CPU-Server installieren und Piper HTTP sowie separate CPU-Wyoming-`stt.*`-Entität testen.
3. **HA-Integration und Pipeline:** Nach HA-Core-Neustart die drei **TAFA Lokal**-Router prüfen, bestehende Automationen/Pipelines unverändert lassen.
4. **Android:** Aktuelle **signierte** Device Bridge installieren, Nicht-Admin-Raumkonto verbinden, Mikrofonmodus/Rufwort prüfen, Bluetooth-Echo-Medienausgabe mit einer echten Frage testen.
5. **GPU optional:** Windows-/Linux-Worker prüfen, GPU-JSON unter **Verbindungen** importieren, GPU-Wyoming und Ollama **in HA** hinzufügen. GPU aus-/einschalten und CPU-Whisper-/Piper-Fallback testen. Ein CPU-LLM-Fallback ist nicht automatisch vorhanden.
6. **Multiroom:** Mindestens zwei physische Tablets/Räume getrennt koppeln, gleichzeitige Fragen/Raumzuordnung kontrollieren. Kamera/Vision ausdrücklich nur optional und nach Freigabe testen.
7. **Alexa-MP3 optional:** HTTPS-Audio-Datei über externen Weg prüfen, interne Generatorports gesperrt halten. Normale Bluetooth-Audioausgabe darf davon nicht abhängen.
8. **Update/Migration:** App-verwaltete Integration von Marketplace-/Alt-Jarvis-Installationen unterscheiden; Rollback und Datenbeständigkeit auf einer gesicherten Testinstanz kontrollieren.

**Freigabestatus:** Ohne die dokumentierten echten Hardware-/Netzwerktests keine pauschale Aussage zu „vollständig getestet“ oder „zertifiziert“. Bekannte Einschränkungen und konkrete Testergebnisse zu jedem Release separat dokumentieren.
