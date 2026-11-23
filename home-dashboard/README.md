# TAFA Home Dashboard · 0.2.0 Preview

**English** | [Deutsch](README.de.md) · [TAFA project](../README.md)

Optional, responsive, configurable Lovelace dashboard inspired by the original Hauszentrale. It runs independently of the original kiosk. No private household configuration is distributed.

## Features

- Original Hauszentrale visual design: compact header and clock, weather hero, live energy metrics, cheapest contiguous two-hour tariff window (requires supported 15-minute tariff attributes), grouped navigation with fixed mobile bottom bar and desktop sidebar, everyday/device/heating rows.

- 14 optional modules and 39 configurable data roles; one or multiple sources depending on the role.
- Visual configuration editor with domain/unit checks, name-based suggestions, source filtering, module ordering, theme, accent, density, English/German language and local configuration import/export.
- Live overview, solar power/yield/forecast totals (W/kW and Wh/kWh normalized), configurable signed grid reading, measured energy flow. Missing readings remain missing; do not map overlapping meters.
- Lights grouped by HA areas, native HA light controls, history graphs, selected camera previews, weather forecasts, waste calendars and shopping-list cards.
- Heating, heat pump, fuel level, EV, appliance and battery readings; select the data from your own existing integrations.
- Optional Echo Relay Assist card. It mounts only after the explicit **Load assistant** action on the assistant page; use one active Echo Relay controller per helper pair. This dashboard never automatically starts listening, services or cameras. Open a camera detail explicitly to request the selected live previews; use only cameras you are authorized to view.

## Installation

1. Download `www/tafa-home/dashboard.js` and `www/tafa-home/model.js` from this directory and copy both to `/config/www/tafa-home/`.
2. In HA Settings → Dashboards → Resources, register `/local/tafa-home/dashboard.js?v=0.2.0` as a JavaScript module. Hard-refresh the browser. Do not overwrite your existing dashboard or load two versions of this card.
3. Create a new storage dashboard called TAFA Home Dashboard with a panel view. Add a manual card:
   ```yaml
   type: custom:tafa-home-dashboard
   version: 1
   modules: []
   bindings: {}
   language: auto
   theme: dark
   density: comfortable
   accent: teal
   gridSign: import
   ```
4. In the native Lovelace card editor, choose modules and map the data sources. Verify units and entity meanings. Export the configuration locally if desired. Select the correct grid sign before comparing import/export values. The card reads only HA data it can access; it does not create devices, helpers or automations.
5. Optional: install the TAFA Echo Relay Assist card and its dependencies using the [dashboard/automation instructions](../docs/en/ha-automations.md). Configure the pipeline IDs if needed. No camera or microphone session starts on the dashboard home page.

## Validation and limitations

Run `node tests.mjs` with a current Node.js version. Tests cover the normalized configuration, role validation, missing entities, unit conversion, grid sign, locale, escaped friendly names, native card configs and synthetic HTML rendering. The files are installed as a separate dashboard in an existing HA instance; screen rendering on a physical tablet and fresh-install testing remain outstanding.

This is a portable development preview, not a feature-complete release of the old kiosk. Advanced Tibber cost reconstruction, intelligent energy planning and device programme learning, specialised heating/L3 detection, tank calibration, and cross-page voice/infobox behavior still require generic modules. It uses existing HA sensors rather than replacing the user's automation logic. The native camera preview and speech are opt-in. Do not share real exported household bindings or backup archives in public issues.
