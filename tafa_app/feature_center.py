"""Optional TAFA feature catalogue and guided Home Assistant source assignment.

The Supervisor token stays on the App backend; the browser only sees entity
IDs, friendly names, units and current availability from the authenticated
local Home Assistant API. Existing source JSON is merged, never replaced.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request

from speech_source import SOURCE_DOMAINS, ROOMS, _advanced, load_options

CORE_API = "http://supervisor/core/api/"
ENTITY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z0-9_]+$")
MODULES = frozenset(("lights", "energy", "battery", "ev", "heating", "heatpump",
                     "fuel", "appliances", "cameras", "waste", "shopping",
                     "weather", "assist", "custom"))
# Stable feature IDs are not translated. New releases add entries here,
# never insert household-specific IDs or modify saved feature selections.
FEATURES = (
    ("heating", "Heizung", "Heating", "Vorlauf, Rücklauf und Spreizung", "Flow, return and delta", ("vorlauf", "ruecklauf", "spreizung"), "heating"),
    ("fuel", "Heizöl & Tank", "Fuel & tank", "Bestand und Verbrauch", "Inventory and consumption", ("heizoel", "oelverbrauch"), "fuel"),
    ("energy", "Strom & PV", "Electricity & solar", "Tarife, Netz und Solarertrag", "Tariffs, grid and solar", ("preis", "guenstig", "netz", "solar", "prognose", "solarheute", "netzheute", "einspeisungheute"), "energy"),
    ("heatpump", "Wärmepumpe", "Heat pump", "Leistung, Energie und Kosten", "Power, energy and cost", ("waermepumpe", "wpheute", "wpkosten"), "heatpump"),
    ("appliances", "Haushaltsgeräte", "Appliances", "Waschmaschine und Kühlschrank", "Washer and refrigerator", ("waschmaschine", "waschkosten", "waschenergie", "kuehlschrank", "kuehlschrankheute"), "appliances"),
    ("waste", "Abfallkalender", "Waste collection", "Abholtermine", "Collection dates", ("restmuell", "bioabfall", "papier", "wertstoff"), "waste"),
    ("weather", "Wetter", "Weather", "Wetterintegration", "Weather integration", ("weather",), "weather"),
    ("shopping", "Einkaufsliste", "Shopping", "Home-Assistant-Aufgabenliste", "Home Assistant to-do list", ("shopping",), "shopping"),
    ("cameras", "Kameras & Vision", "Cameras & vision", "Kameras im Dashboard-Editor auswählen", "Select cameras in the dashboard editor", (), "cameras"),
    ("ev", "Wallbox & Elektroauto", "EV & charger", "Ladegeräte und Stromverbrauch", "Chargers and energy readings", (), "ev"),
    ("battery", "Batteriespeicher", "Battery storage", "Speicherwerte und Ladezustand", "Storage readings and state of charge", (), "battery"),
    ("lights", "Licht & Räume", "Lights & rooms", "Leuchten und Temperaturen", "Lights and room temperatures", (), "lights"),
    ("assist", "Sprachassistent", "Voice assistant", "TAFA Device Bridge und Sprachfunktionen", "Device Bridge and speech tools", (), "assist"),
)
BY_FEATURE = {item[0]: item for item in FEATURES}
SOURCES = {key for item in FEATURES for key in item[5]}
assert SOURCES == set(SOURCE_DOMAINS), "Every TAFA source needs a feature"

SOURCE_LABELS = {
    "vorlauf": ("Vorlauftemperatur", "Flow temperature"), "ruecklauf": ("Rücklauftemperatur", "Return temperature"),
    "spreizung": ("Spreizung", "Temperature delta"), "heizoel": ("Heizölbestand", "Fuel volume"),
    "oelverbrauch": ("Heizölverbrauch", "Fuel use"), "preis": ("Aktueller Strompreis", "Current electricity price"),
    "guenstig": ("Günstigster Strompreis", "Lowest electricity price"), "netz": ("Netzleistung", "Grid power"),
    "solar": ("PV-Leistung", "Solar power"), "prognose": ("PV-Prognose", "Solar forecast"),
    "solarheute": ("PV-Ertrag heute", "Solar production today"), "netzheute": ("Netzbezug heute", "Grid use today"),
    "einspeisungheute": ("Einspeisung heute", "Export today"),
    "waermepumpe": ("Wärmepumpenleistung", "Heat pump power"),
    "wpheute": ("Wärmepumpenenergie heute", "Heat pump energy today"),
    "wpkosten": ("Wärmepumpenkosten", "Heat pump cost"),
    "waschmaschine": ("Waschmaschinenleistung", "Washer power"), "waschkosten": ("Waschkosten", "Washer cost"),
    "waschenergie": ("Waschmaschinenenergie", "Washer energy"),
    "kuehlschrank": ("Kühlschrankleistung", "Refrigerator power"),
    "kuehlschrankheute": ("Kühlschrankenergie", "Refrigerator energy"),
    "restmuell": ("Restmüll", "Residual waste"), "bioabfall": ("Biotonne", "Organic waste"),
    "papier": ("Papier", "Paper"), "wertstoff": ("Wertstoffe", "Recyclables"),
    "weather": ("Wetterquelle", "Weather entity"), "shopping": ("Einkaufsliste", "Shopping list"),
}
# Validate units before proposing a mapping. Name similarity only changes sort order.
UNITS = {
    "vorlauf": ("°C",), "ruecklauf": ("°C",), "spreizung": ("K", "°C"),
    "heizoel": ("L", "l", "Liter"), "oelverbrauch": ("L", "l", "Liter"),
    "preis": ("ct/kWh", "¢/kWh", "Cent/kWh", "EUR/kWh", "€/kWh"),
    "guenstig": ("ct/kWh", "¢/kWh", "Cent/kWh", "EUR/kWh", "€/kWh"),
    "netz": ("W", "kW"), "solar": ("W", "kW"),
    "prognose": ("Wh", "kWh"), "solarheute": ("Wh", "kWh"),
    "netzheute": ("Wh", "kWh"), "einspeisungheute": ("Wh", "kWh"),
    "waschmaschine": ("W", "kW"), "waschenergie": ("Wh", "kWh"),
    "waermepumpe": ("W", "kW"), "wpheute": ("Wh", "kWh"),
    "kuehlschrank": ("W", "kW"), "kuehlschrankheute": ("Wh", "kWh"),
    "wpkosten": ("EUR", "€", "ct", "Cent"), "waschkosten": ("EUR", "€", "ct", "Cent"),
    "kuehlschrankheute": ("Wh", "kWh"),
}
SEARCH_TERMS = {
    "heizoel": ("heizöl", "heizol", "oil", "tank", "shelly", "bestand"),
    "vorlauf": ("vorlauf", "flow", "heizung"), "ruecklauf": ("rücklauf", "return"),
    "spreizung": ("spreizung", "delta"), "solar": ("solar", "pv", "photovoltaik"),
    "netz": ("netz", "grid", "pulse"), "preis": ("tibber", "preis", "price"),
    "waermepumpe": ("wärmepumpe", "warmepumpe", "heatpump"), "weather": ("weather", "wetter"),
    "shopping": ("einkauf", "todo", "bring"), "restmuell": ("restmüll", "restmuell"),
    "bioabfall": ("bio",), "papier": ("papier",), "wertstoff": ("wertstoff",),
    "waschmaschine": ("wasch", "washer"), "kuehlschrank": ("kühlschrank", "kuehlschrank"),
}


def _ha_json(token, path, *, limit=6_000_000):
    """Read bounded data only from the fixed Supervisor Core API."""
    if not token:
        raise RuntimeError("Home Assistant API unavailable")
    req = urllib.request.Request(CORE_API + path, headers={"Authorization": "Bearer " + token,
                                                         "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=7) as response:
        if response.status != 200 or response.headers.get("Content-Length", "0").isdigit() and int(response.headers.get("Content-Length", "0")) > limit:
            raise RuntimeError("HA source list unavailable")
        payload = response.read(limit + 1)
        if len(payload) > limit:
            raise RuntimeError("HA source list too large")
        return json.loads(payload)


def discover_entities(token):
    """Return safe display metadata; never expose attributes or credentials."""
    try:
        rows = _ha_json(token, "states")
    except (ValueError, OSError, RuntimeError, urllib.error.URLError):
        return [], False
    if not isinstance(rows, list):
        return [], False
    result = []
    for raw in rows[:5000]:
        if not isinstance(raw, dict):
            continue
        ident = raw.get("entity_id", "")
        if not isinstance(ident, str) or not ENTITY_RE.fullmatch(ident):
            continue
        if ident.split(".", 1)[0] not in {"sensor", "weather", "todo", "switch", "schedule", "camera", "light", "climate"}:
            continue
        attributes = raw.get("attributes") if isinstance(raw.get("attributes"), dict) else {}
        unit = attributes.get("unit_of_measurement") or ""
        if not isinstance(unit, str):
            unit = ""
        label = attributes.get("friendly_name") or ident
        result.append({"id": ident, "name": str(label)[:120],
                       "unit": unit[:24], "online": raw.get("state") not in ("unknown", "unavailable", None)})
    return result, True


def eligible(key, entry):
    if key not in SOURCE_DOMAINS or not isinstance(entry, dict):
        return False
    if not entry.get("id", "").startswith(SOURCE_DOMAINS[key] + "."):
        return False
    return key not in UNITS or entry.get("unit", "") in UNITS[key]


def ordered_candidates(key, entities, selected=""):
    relevant = [e for e in entities if eligible(key, e)]
    terms = SEARCH_TERMS.get(key, (key,))
    def score(item):
        label = (item["id"] + " " + item["name"]).lower()
        return (sum(3 if term in label else 0 for term in terms) + (1 if item.get("online") else 0))
    # The selected value always remains shown even if the sensor is offline.
    return sorted(relevant, key=lambda e: (-score(e), e["name"].lower(), e["id"]))[:750]


def _selected(options):
    try:
        d = json.loads(options.get("sources_json", "{}") or "{}")
    except (TypeError, ValueError):
        return {}
    return d if isinstance(d, dict) else {}


def save_source_group(fields, options, entities):
    feature_id = _single(fields, "feature_id")
    feature = BY_FEATURE.get(feature_id)
    if feature is None or not feature[5]:
        raise ValueError("Unbekannte TAFA-Funktion")
    keys = feature[5]
    allowed = {"csrf", "lang", "tab", "action", "feature_id"} | {"source_" + k for k in keys}
    if set(fields) - allowed or len(fields.get("feature_id", [])) != 1:
        raise ValueError("Ungültige Zuordnung")
    current = _selected(options)
    updates = dict(current)
    by_id = {e["id"]: e for e in entities}
    for key in keys:
        raw = _single(fields, "source_" + key).strip()
        if not raw:
            updates.pop(key, None)
            continue
        domain = SOURCE_DOMAINS[key]
        if not ENTITY_RE.fullmatch(raw) or not raw.startswith(domain + "."):
            raise ValueError("Ungültige Entität")
        if raw in by_id:
            if not eligible(key, by_id[raw]):
                raise ValueError("Entität hat den falschen Typ oder die falsche Einheit")
        elif raw != current.get(key):
            raise ValueError("Neue Entität ist in Home Assistant nicht verfügbar")
        updates[key] = raw
    # Do not clear another category, even when that integration is not installed.
    from speech_source import setup_settings_values
    proposed = {**options, "sources_json": json.dumps(updates, ensure_ascii=False)}
    setup_settings_values(proposed)
    return {"sources_json": proposed["sources_json"]}


def _single(fields, key):
    items = fields.get(key, [])
    if len(items) != 1 or not isinstance(items[0], str):
        raise ValueError("Fehlende oder doppelte Eingabe: " + key)
    return items[0]


def _esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def render_feature_center(options, lang, csrf, entities, can_read, active=None):
    en = lang == "en"
    t = lambda de, eng: eng if en else de
    assigned = _selected(options)
    active = set(active or ())
    blocks = []
    for feature_id, title_de, title_en, sub_de, sub_en, keys, module in FEATURES:
        filled = sum(bool(assigned.get(k)) for k in keys)
        installed = "data-ready" if keys and filled == len(keys) else "data-partial" if filled else "data-empty"
        status = t("Vollständig zugeordnet", "All sources assigned") if keys and filled == len(keys) else (
            t(f"{filled}/{len(keys)} Quellen zugeordnet", f"{filled}/{len(keys)} sources assigned") if keys else
            t("Optionales Dashboard-Modul", "Optional dashboard module"))
        source_fields = []
        for key in keys:
            value = assigned.get(key, "")
            entries = ordered_candidates(key, entities, value)
            present = any(item["id"] == value for item in entries)
            options_html = [f'<option value="">{t("Nicht zugeordnet", "Unassigned")}</option>']
            if value and not present:
                options_html.append(f'<option value="{_esc(value)}" selected>{_esc(value)} · {t("momentan nicht gefunden", "currently missing")}</option>')
            for item in entries:
                display = item["name"] + (" · " + item["unit"] if item["unit"] else "")
                display += " · " + item["id"]
                if not item.get("online"):
                    display += t(" (offline)", " (offline)")
                options_html.append(f'<option value="{_esc(item["id"])}"'
                                    f'{" selected" if item["id"] == value else ""}>{_esc(display)}</option>')
            source_fields.append(
                f'<label class="feature-source"><span>{_esc(SOURCE_LABELS[key][int(en)])}</span>'
                f'<input type="search" data-filter-select="source_{_esc(key)}"'
                f' placeholder="{_esc(t("Sensoren filtern", "Filter sensors"))}" aria-label="{_esc(SOURCE_LABELS[key][int(en)])}">'
                f'<select name="source_{_esc(key)}" data-source-picker="source_{_esc(key)}">'
                + "".join(options_html) + '</select></label>')
        form = ""
        if keys:
            form = (f'<form action="./" method="post" class="feature-form">'
                    f'<input type="hidden" name="csrf" value="{_esc(csrf)}">'
                    f'<input type="hidden" name="lang" value="{_esc(lang)}">'
                    '<input type="hidden" name="tab" value="features">'
                    '<input type="hidden" name="action" value="feature_sources">'
                    f'<input type="hidden" name="feature_id" value="{_esc(feature_id)}">'
                    + "".join(source_fields) +
                    f'<button class="btn btn-primary" type="submit">{t("Zuordnungen speichern", "Save sources")}</button></form>')
        else:
            form = f'<p class="subtle">{t("Geräte und Sensoren anschließend im TAFA-Dashboard-Editor auswählen.", "Choose devices and sensors in the TAFA dashboard editor after enabling.")}</p>'
        button = ('<form action="./" method="post">'
                  f'<input type="hidden" name="csrf" value="{_esc(csrf)}">'
                  f'<input type="hidden" name="lang" value="{_esc(lang)}">'
                  '<input type="hidden" name="tab" value="features">'
                  '<input type="hidden" name="action" value="feature_add">'
                  f'<input type="hidden" name="feature_id" value="{_esc(feature_id)}">'
                  f'<button class="btn btn-outline" type="submit"'
                  + (" disabled" if module in active else "") + ">"
                  + (t("Im Dashboard enthalten", "Already on dashboard") if module in active
                     else t("Zum TAFA-Dashboard hinzufügen", "Add to TAFA dashboard"))
                  + "</button></form>")
        blocks.append(
            f'<article class="feature-card" id="feature-{_esc(feature_id)}" {installed}>'
            '<div class="feature-heading"><div>'
            f'<h3>{_esc(title_en if en else title_de)}</h3>'
            f'<p>{_esc(sub_en if en else sub_de)}</p></div>'
            f'<span class="feature-status">{_esc(status)}</span></div>'
            f'<details><summary>{t("Sensoren und Voraussetzungen verwalten", "Manage sources and requirements")}</summary>'
            + form + '</details>' + button + '</article>')
    info = (t("Die Auswahl wird mit den vorhandenen HA-Entitäten abgeglichen. Nicht eingerichtete Funktionen bleiben optional; bestehende Zuordnungen gehen nicht verloren.",
              "Selections are checked against existing HA entities. Missing integrations are optional and existing mappings are preserved.")
            if can_read else
            t("Home Assistant antwortet gerade nicht. Bereits zugeordnete Quellen bleiben erhalten. Neue Zuordnungen sind erst nach erneuter Verbindung möglich.",
              "Home Assistant is temporarily unavailable. Existing sources are kept; adding new sources requires reconnecting."))
    return (
        '<div class="feature-intro"><h3>'
        + t("Funktionen nach Bedarf", "Enable only what you need") + '</h3>'
        + f'<p>{_esc(info)}</p>'
        + f'<p class="muted">{t("Neue Funktionen erscheinen hier mit Updates. Das Hinzufügen verändert keine bestehenden Dashboard-Kacheln oder Automationen.", "New features appear here after updates. Adding one never alters existing tiles or automations.")}</p>'
        + '</div><div class="feature-grid">' + "".join(blocks) + '</div>'
        + '<details class="support-disclosure"><summary>'
        + t("Erweiterte Konfiguration und Backups", "Advanced configuration and backups")
        + '</summary><p>' + t("JSON bleibt nur für Export, Import und Fehlerdiagnose verfügbar. Die TAFA-App speichert die Zuordnung intern automatisch.",
                                "JSON is reserved for export, import and troubleshooting. TAFA stores mappings internally.")
        + '</p><pre class="feature-json">' + _esc(json.dumps(assigned, ensure_ascii=False, indent=2)) + '</pre></details>'
    )


def _dashboard_command(token, command, config=None):
    """Use existing admin-authenticated HA WebSocket; do not touch Lovelace files."""
    if not token:
        raise RuntimeError("TAFA Home Assistant connection unavailable")
    from websockets.sync.client import connect
    with connect("ws://supervisor/core/websocket", open_timeout=6, close_timeout=2) as ws:
        hello = json.loads(ws.recv(timeout=8))
        if hello.get("type") != "auth_required":
            raise RuntimeError("HA WebSocket unavailable")
        ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(ws.recv(timeout=8)).get("type") != "auth_ok":
            raise RuntimeError("HA WebSocket authorization failed")
        payload = {"id": 1, "type": "tablet_assist_for_alexa/dashboard/" + command}
        if config is not None:
            payload["config"] = config
        ws.send(json.dumps(payload))
        while True:
            reply = json.loads(ws.recv(timeout=10))
            if reply.get("id") != 1:
                continue
            if not reply.get("success"):
                raise RuntimeError("TAFA dashboard not available; install or restart TAFA first")
            return reply.get("result") or {}


def active_dashboard_modules(token):
    try:
        result = _dashboard_command(token, "get")
        cfg = result.get("config")
        if not isinstance(cfg, dict):
            raise ValueError("Invalid dashboard response")
        modules = cfg.get("modules", [])
        return modules if isinstance(modules, list) else []
    except (RuntimeError, OSError, ValueError, TimeoutError, KeyError):
        return []


def add_dashboard_module(token, feature_id):
    """Add just one existing, known module; never reset tiles or mappings."""
    feature = BY_FEATURE.get(feature_id)
    if feature is None or feature[6] not in MODULES:
        raise ValueError("Unknown TAFA module")
    data = _dashboard_command(token, "get")
    cfg = data.get("config")
    if not isinstance(cfg, dict) or not isinstance(cfg.get("modules"), list):
        raise RuntimeError("TAFA dashboard configuration not available")
    name = feature[6]
    if name in cfg["modules"]:
        return False
    if len(cfg["modules"]) >= len(MODULES):
        raise ValueError("Dashboard already has all available modules")
    # Copy only modules; do not rewrite the user's bindings/presentation/layout.
    updated = dict(cfg)
    updated["modules"] = [*cfg["modules"], name]
    _dashboard_command(token, "set", updated)
    return True
