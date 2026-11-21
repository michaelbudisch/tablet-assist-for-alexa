"""Read current local weather or actual HA forecast rows."""
from datetime import timedelta
from homeassistant.util import dt as dt_util
import math

CONDITIONS={"clear-night":"klar","cloudy":"bewölkt","exceptional":"außergewöhnlich","fog":"neblig","hail":"Hagel","lightning":"Gewitter","lightning-rainy":"Gewitter mit Regen","partlycloudy":"teilweise bewölkt","pouring":"starker Regen","rainy":"Regen","snowy":"Schnee","snowy-rainy":"Schneeregen","sunny":"sonnig","windy":"windig","windy-variant":"windig und bewölkt"}
RAIN={"rainy","pouring","lightning-rainy","snowy-rainy"}
SNOW={"snowy","snowy-rainy"}
WEEKDAYS=("Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag")
CURRENT={"aktuell","temperatur","feuchte","wind","druck","gefuehlt","regenjetzt","regenwahrscheinlichkeit"}
DAILY={"heute","morgen","uebermorgen","kommendetage","frost","regenuebermorgen"}
HOURLY={"regenheute","regenmorgen","regennachher","regenzwei","regenabend","regennacht","regenmorgenfrueh","schnee","schneeheute","schneemorgen","abend","nacht","morgenfrueh","stunden"}
WEATHER_KEYS=CURRENT|DAILY|HOURLY

def numeric(v):
    try:
        n=float(v)
        return n if math.isfinite(n) else None
    except (TypeError,ValueError):return None

def value(v,unit):
    n=numeric(v)
    if n is None:return None
    return f"{n:.1f}".rstrip("0").rstrip(".").replace(".",",")+" "+unit

def description(r,tu,pu):
    parts=[CONDITIONS.get(r.get("condition"),"unbekannter Wetterzustand")]
    for field,label,unit in (("temperature","Temperatur",tu),("templow","Tiefsttemperatur",tu),("precipitation","Niederschlag",pu)):
        if (v:=value(r.get(field),unit)):parts.append(label+" "+v)
    return ", ".join(parts)

async def weather(hass,entity,kind,context,now=None):
    now=now or dt_util.now()
    state=hass.states.get(entity)
    if not state or state.state in ("unknown","unavailable"):return "Wetterdaten sind momentan nicht verfügbar."
    a=state.attributes
    tu={"°C":"Grad Celsius","°F":"Grad Fahrenheit"}.get(a.get("temperature_unit"),a.get("temperature_unit","Grad"))
    pu={"mm":"Millimeter","in":"Zoll"}.get(a.get("precipitation_unit"),a.get("precipitation_unit",""))
    if kind in CURRENT:
        if kind=="regenjetzt":return "Laut Wetterdienst: "+CONDITIONS.get(state.state,"unbekannter Wetterzustand")+"."
        if kind=="regenwahrscheinlichkeit":return "Die Regenwahrscheinlichkeit für den gewünschten Zeitraum ist nicht als gesicherter Wert verfügbar. Frage nach der Regenvorhersage."
        fields={"temperatur":("temperature",tu,"Außentemperatur"),"feuchte":("humidity","Prozent","Luftfeuchtigkeit"),"wind":("wind_speed",a.get("wind_speed_unit",""),"Windgeschwindigkeit"),"druck":("pressure",a.get("pressure_unit",""),"Luftdruck"),"gefuehlt":("apparent_temperature",tu,"Gefühlte Temperatur")}
        if kind in fields:
            field,unit,label=fields[kind]
            v=value(a.get(field),unit)
            return label+": "+v+"." if v else label+" ist momentan nicht verfügbar."
        return "Aktuell: "+description({"condition":state.state,"temperature":a.get("temperature")},tu,pu)+"."
    mode="daily" if kind in DAILY else "hourly"
    data=await hass.services.async_call("weather","get_forecasts",{"entity_id":entity,"type":mode},blocking=True,return_response=True,context=context)
    rows=data[entity]["forecast"]
    valid=[]
    for r in rows:
        ts=dt_util.parse_datetime(str(r.get("datetime","")))
        if ts is not None and ts.tzinfo is not None:valid.append((dt_util.as_local(ts),r))
    valid.sort(key=lambda p:p[0])
    if kind in DAILY:
        offset=2 if kind in ("uebermorgen","regenuebermorgen") else 0 if kind=="heute" else 1
        d=now.date()+timedelta(days=offset)
        n=3 if kind=="kommendetage" else 1
        hits=[(ts,r) for ts,r in valid if d<=ts.date()<d+timedelta(days=n)]
        if not hits:return "Für diesen Zeitraum gibt es keine Tagesvorhersage."
        if kind=="frost":
            if a.get("temperature_unit") not in ("°C","°F"):return "Die Temperatureinheit ist für die Frostvorhersage nicht bekannt."
            low=numeric(hits[0][1].get("templow"))
            if low is None:return "Für morgen fehlt die Tiefsttemperatur."
            threshold=32 if a.get("temperature_unit")=="°F" else 0
            return "Morgen: Tiefsttemperatur "+value(low,tu)+(". Luftfrost ist möglich." if low<=threshold else ". Luftfrost wird nicht erwartet.")
        return "; ".join(WEEKDAYS[ts.weekday()]+": "+description(r,tu,pu) for ts,r in hits[:n]) + (". Weitere Tagesdaten fehlen." if len(hits)<n else ".")
    midnight=now.replace(hour=0,minute=0,second=0,microsecond=0); start=now; end=now+timedelta(hours=6)
    if kind in ("regenheute","schneeheute"):end=midnight+timedelta(days=1)
    elif kind in ("regenmorgen","schneemorgen"):start=midnight+timedelta(days=1);end=start+timedelta(days=1)
    elif kind in ("regenmorgenfrueh","morgenfrueh"):start=midnight+timedelta(days=1,hours=6);end=start+timedelta(hours=6)
    elif kind in ("regenabend","abend"):start=max(now,midnight+timedelta(hours=18));end=midnight+timedelta(days=1)
    elif kind in ("regennacht","nacht"):end=midnight+timedelta(hours=6,days=int(now.hour>=6))
    elif kind=="regenzwei":end=now+timedelta(hours=2)
    elif kind=="schnee":end=now+timedelta(hours=24)
    hits=[(ts,r) for ts,r in valid if start<=ts<end]
    if not hits:return "Für diesen Zeitraum gibt es keine stündliche Wettervorhersage."
    if kind.startswith(("regen","schnee")):
        snow=kind.startswith("schnee"); target=SNOW if snow else RAIN
        label="Schnee oder Schneeregen" if snow else "Regen oder Schneeregen"
        for ts,r in hits:
            if r.get("condition") in target:return label+" wird laut Stundenprognose erwartet, erstmals "+WEEKDAYS[ts.weekday()]+" gegen "+ts.strftime("%H:%M")+" Uhr."
        if any(r.get("condition") not in CONDITIONS for _,r in hits):return "Die Stundenprognose ist unvollständig."
        if not snow and any((numeric(r.get("precipitation")) or 0)>0 for _,r in hits):return "Niederschlag wird erwartet, aber nicht eindeutig als Regen ausgewiesen."
        return "In den "+str(len(hits))+" verfügbaren Stundenwerten für diesen Zeitraum wird "+("kein Schnee" if snow else "kein Regen")+" gemeldet."
    temps=[v for _,r in hits if (v:=numeric(r.get("temperature"))) is not None]
    return "Laut Stundenprognose zunächst "+CONDITIONS.get(hits[0][1].get("condition"),"unbekannt")+ (". Temperaturen zwischen "+value(min(temps),tu)+" und "+value(max(temps),tu) if temps else "")+"."
