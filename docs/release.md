# TAFA — Tests und Release-Checkliste

[English](en/release.md) | **Deutsch** · [Projektübersicht](../README.de.md)

**Aktueller Stand:** TAFA Home-Assistant-App **0.3.11** (experimenteller Release-Kandidat), gemeinsame HA-Integration **0.4.3**, Android Device Bridge **1.0.0 unverändert**. Keine Produktions-/Hardwarefreigabe.

## Automatisierte Prüfungen

Die GitHub-Actions-Workflows im Repository prüfen:

- `python scripts/test_unified_layout.py`: nur eine Integration, vollständiger App-/Marketplace-Bundle-Abgleich, keine Platzhalter/privaten Netzwerkadressen, Legacy-API-Schnittstellen vorhanden
- `python -m unittest discover -s tafa_app/tests -v`: sicherer Installer und Rollback, CSRF/Ingress, Piper-/Whisper-HTTP-API und HA-Config-/Assist-Pipeline-Mocks
- `node --input-type=module --check < custom_components/tablet_assist_for_alexa/frontend/panel.js`: JavaScript-Syntax
- `python tests/test_marketplace.py` sowie HACS/hassfest: Integrationsformat und Abhängigkeiten
- `bash tests/ha_e2e/run.sh`: realer Home-Assistant-Core-Dockerstart mit Setup, nativen Relay-Diensten, Multiroom-, Kamera-/Bewegungs-Entitäten, Konversationsfluss, Neustart und persistenter Erinnerung
- Docker-Buildmatrix für `linux/amd64` und `linux/arm64` in `.github/workflows/tafa-app.yml`.

Frühere erfolgreiche CI-Läufe beweisen **Quellcode-/Container-/HA-Core-Tests**, aber nicht den kompletten Betrieb auf Home Assistant OS mit Supervisor-Ingress, frisch heruntergeladenen CPU-Modellen und physischer Tablet-/Echo-Hardware. Bei jeder Codeänderung den aktuellen Head-Commit separat prüfen.

## Offene Blocker für einen stabilen Release

1. Eine vollständige Installation auf einem *frischen* Home Assistant OS inkl. App-Store, Supervisor-API, Ingress und automatischer Pipeline testen.
2. Piper-/Whisper-Download, RAM-/CPU-Bedarf und Sprachqualität auf amd64 und arm64 real prüfen.
3. Bluetooth-Wiedergabe über Echo sowie zwei echte Android-Geräte gleichzeitig testen.
4. **Rufwortübergabe:** Die unveränderte Device Bridge 1.0.0 meldet nur das erkannte Rufwort und gibt ihr Mikrofon frei, überträgt aber nicht die anschließende Frage. Ein separat aktiver Assist-Client muss diese aufnehmen. Vollständig freihändiger Betrieb mit nur TAFA und dieser Bridge ist derzeit nicht möglich; nicht als fertig ausgeben.
5. Altinstallationsmigration mit vorhandenen `jarvis_tablet_audio`-Einträgen und Raumzuordnungen auf Testkopien prüfen. Bestehende produktive Systeme nicht überschreiben.
6. Sicherheits-/Lizenzprüfung der CPU-Stimmen und Drittanbieterbibliotheken, anschließend erst stabiles Release-Tag erstellen.

**Release-Policy:** Versionsstand, App-Manifest, `VERSION`, Changelogs und zweisprachige Anleitungen synchron halten. Das private Dashboard, Haushaltskonfigurationen, Tokens und Android-APK-Änderungen bleiben ausgeschlossen.

[App-Installation](app.md) · [Marketplace](marketplace.md) · [Backend](backend-roadmap.md) · [GitHub Actions](https://github.com/michaelbudisch/tablet-assist-for-alexa/actions).
