"""Semantic source keys, never household-specific entity IDs."""
SOURCES = {
    "weather": "weather", "shopping": "todo",
    "restmuell": "sensor", "bioabfall": "sensor", "papier": "sensor", "wertstoff": "sensor",
    "vorlauf": "sensor", "ruecklauf": "sensor", "spreizung": "sensor",
    "preis": "sensor", "guenstig": "sensor",
    "netz": "sensor", "solar": "sensor", "prognose": "sensor",
    "solarheute": "sensor", "netzheute": "sensor", "einspeisungheute": "sensor",
    "heizoel": "sensor", "oelverbrauch": "sensor",
    "waschmaschine": "sensor", "waschkosten": "sensor", "waschenergie": "sensor",
    "waermepumpe": "sensor", "wpheute": "sensor", "wpkosten": "sensor",
    "kuehlschrank": "sensor", "kuehlschrankheute": "sensor",
}
WASTE_LABELS = {"restmuell":"Restmüll", "bioabfall":"Biotonne", "papier":"Papiertonne", "wertstoff":"Gelbe Tonne"}
# label, allowed explicit units. No guessing from a number without a unit.
METRICS = {
    "vorlauf": ("Vorlauftemperatur", ("°C",)),
    "ruecklauf": ("Rücklauftemperatur", ("°C",)),
    "spreizung": ("Temperaturdifferenz", ("K","°C")),
    "preis": ("Aktueller Strompreis pro Kilowattstunde", ("ct/kWh","¢/kWh","Cent/kWh","EUR/kWh","€/kWh")),
    "guenstig": ("Niedrigster Strompreis für morgen", ("ct/kWh","¢/kWh","Cent/kWh","EUR/kWh","€/kWh")),
    "netz": ("Aktuelle Netzleistung", ("W","kW")),
    "solar": ("Aktuelle Solarleistung", ("W","kW")),
    "prognose": ("Erwarteter Solarertrag morgen", ("kWh","Wh")),
    "solarheute": ("Gemessener Solarertrag heute", ("kWh","Wh")),
    "netzheute": ("Netzbezug heute", ("kWh","Wh")),
    "einspeisungheute": ("Netzeinspeisung heute", ("kWh","Wh")),
    "heizoel": ("Heizölbestand", ("L","l","Liter")),
    "oelverbrauch": ("Geschätzter Heizölverbrauch heute", ("L","l","Liter")),
    "waschmaschine": ("Aktuelle Waschmaschinenleistung", ("W","kW")),
    "waschkosten": ("Erfasste Waschmaschinenkosten heute", ("EUR","€","ct","Cent")),
    "waschenergie": ("Erfasster Waschmaschinenverbrauch heute", ("kWh","Wh")),
    "waermepumpe": ("Aktuelle Wärmepumpenleistung", ("W","kW")),
    "wpheute": ("Wärmepumpenverbrauch heute", ("kWh","Wh")),
    "wpkosten": ("Erfasste Wärmepumpenkosten heute", ("EUR","€","ct","Cent")),
    "kuehlschrank": ("Aktuelle Kühlschrankleistung", ("W","kW")),
    "kuehlschrankheute": ("Kühlschrankverbrauch heute", ("kWh","Wh")),
}
UNITS = {"°C":"Grad Celsius","K":"Kelvin","W":"Watt","kW":"Kilowatt","Wh":"Wattstunden","kWh":"Kilowattstunden","L":"Liter","l":"Liter","Liter":"Liter","EUR":"Euro","€":"Euro","ct":"Cent","Cent":"Cent","ct/kWh":"Cent pro Kilowattstunde","¢/kWh":"Cent pro Kilowattstunde","Cent/kWh":"Cent pro Kilowattstunde","EUR/kWh":"Euro pro Kilowattstunde","€/kWh":"Euro pro Kilowattstunde"}
