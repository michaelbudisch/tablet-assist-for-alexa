# TAFA-Frontend: feste Dateinamen, Builds und sichere Bereinigung

Diese Regeln gelten für **das private Home-Assistant-Dashboard**. Die ausgelieferte Integration unter `custom_components/tablet_assist_for_alexa/frontend/` ist ein getrenntes Produkt und hat eigene Dateien.

## Private Home-Assistant-Dateien

| Aufgabe | Fester Pfad unter /config/www |
| --- | --- |
| Hauszentrale | `tafa/hauszentrale-main.js` |
| Ambient-Modus | `tafa/ambient-night.js` |
| Ambient-Übersicht | `tafa/ambient-overview.js` |
| Update-Prüfung | `tafa/frontend-update-guard.js` |
| Zentrale Build-Version | `tafa/frontend-build.json` |
| Sprachmodul | `tafa/modules/voice/tafa-dashboard-voice.js` |
| Touch-Editor / Widgets | `tafa-touch-editor.js` / `tafa-widget-library.js` |

**Ab sofort keine neuen** `hauszentrale-main-v0.x.js`, `ambient-night-v0.x.js`, `frontend-update-guard-v0.x.js` oder `tafa-touch-editor-v1.x.js` anlegen. Bestehende Dateien überschreiben. Die Historie gehört in Git oder ein ZIP außerhalb von `www/`.

## Verbindlicher Ablauf bei jeder Frontend-Änderung

1. Live-Stand, registrierte Lovelace-Ressourcen und `frontend-build.json` lesen. Dynamische JS-Imports und eventuelle parallele Änderungen prüfen.
2. Zuerst stabile Abhängigkeiten aktualisieren, danach die feste Hauptdatei. Vorherige Textfassungen durch MCP-Datei-Backup sichern.
3. JS-Syntax und alle referenzierten `/local/...`-Dateien prüfen. Keine nicht mehr vorhandenen `/local/jarvis/...`-Ressourcen importieren.
4. **Eine einzige neue Build-Version** festlegen. Sie in Cache-Parametern der Ressourcen und dynamischer Imports (`?v=0.5.11`) synchronisieren.
5. Die Ressource `/local/tafa/hauszentrale-main.js?v=...`, Ambient-Ressource und Update-Guard registrieren. `frontend-build.json` zuletzt aktualisieren.
6. Nachprüfung: Registrierte Hauptressource und Manifest stimmen überein; Dashboard und Ambient laden; Rufwort-Status läuft; nach Browser-Neuladen keine veralteten Versionsmeldungen.
7. Erst dann verwaiste Versionen mit geprüftem ZIP-Rollback entfernen. Nur **ein** lokaler Rückfallstand je Familie.

Private Nutzer-Dashboards, Automatisierungen und Sensoren dürfen **nicht** ungefragt in die öffentliche TAFA-Integration kopiert oder bei Updates überschrieben werden.

## Cleanup-Befehle (auf einem System mit Zugriff auf Home Assistant /config)

```bash
python3 scripts/tafa_frontend_cleanup.py --repo-check
python3 scripts/tafa_frontend_cleanup.py --config /config
python3 scripts/tafa_frontend_cleanup.py --config /config --apply
```

**Ohne `--apply` nur Prüfung, keine Änderungen.** Mit `--apply` muss die aktive Lovelace-Ressourcenregistrierung lesbar und das Manifest konsistent sein. Das Programm schreibt vor jedem Entfernen ein ZIP mit SHA-256-Nachweisen unter `/config/backups/tafa-frontend-legacy-*.zip` (außerhalb des HTTP-Webroots). Die ZIP-Datei lässt sich bei Bedarf in `/config` entpacken. Das Programm schreibt niemals in `.storage`, Automatisierungen oder andere HA-Konfigurationen.

## Zusätzliche Prüfpflichten

- `www/tafa-home/`: alte Entwicklungsansicht, nicht automatisch Teil des ausgelieferten Dashboards.
- Verbliebene `jarvis`-IDs erst nach Verbraucherprüfung umstellen; nicht allein aufgrund des Namens löschen.
- Für GitHub-Release und TAFA-App die zwei gelieferten Frontend-Spiegel synchron halten: `custom_components/tablet_assist_for_alexa/frontend/` und `tafa_app/bundle/tablet_assist_for_alexa/frontend/`.
- GitHub-Tests und ein Browser-Hard-Reload sind Teil jedes Frontend-Updates.
