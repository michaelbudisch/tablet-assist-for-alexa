# TAFA frontend asset maintenance

The public integration (`custom_components/tablet_assist_for_alexa/frontend/`) and the private Home Assistant dashboard (`/config/www/tafa/`) have distinct release paths; never ship private sensors, room IDs, or dashboard assets as public defaults.

Private assets now use stable filenames: `hauszentrale-main.js`, `ambient-night.js`, `ambient-overview.js`, `frontend-update-guard.js` and `modules/voice/tafa-dashboard-voice.js`. Do not create a new `-v0.x.js` file for each edit. Update the existing file and use versioned URLs (`?v=<build>`).

Deployment order: read the newest live sources and Lovelace resources; update dependencies; syntax-check JavaScript and import paths; update the resource URLs and `frontend-build.json` with **the same** build version (manifest last); verify the browser after a hard reload. Keep one rollback version per file family.

Dry-run and optional safe removal:
```bash
python3 scripts/tafa_frontend_cleanup.py --repo-check
python3 scripts/tafa_frontend_cleanup.py --config /config
python3 scripts/tafa_frontend_cleanup.py --config /config --apply
```

`--apply` needs a readable Home Assistant resource registry and matching build manifest. It creates a verified SHA-256 ZIP outside `www/` before removing obsolete files. It does not modify Lovelace storage, automation definitions or integration configuration. See the [German maintenance guide](../frontend-asset-maintenance.de.md) for details.
