"""Explicit short read-only follow-ups, scoped to a conversation."""
import re
from time import monotonic
from .local_intents import normalize
from .weather_data import WEATHER_KEYS

HEATING={"vorlauf","ruecklauf","spreizung"}
WASTE={"restmuell","bioabfall","papier","wertstoff","muell_naechste","muell_uebersicht","muell_heute","muell_morgen"}
ENERGY={"solar","solarheute","prognose","netz","netzheute","einspeisungheute","preis","guenstig"}
def resolve(previous,text):
    s=normalize(text)
    s=re.sub(r"^(?:und |wie sieht es mit |was ist mit )","",s)
    s=re.sub(r"^(?:der|die|das|dem|den) ","",s)
    s=re.sub(r" (?:aus|bitte)$","",s)
    if previous in HEATING:
        return {"vorlauf":"vorlauf","vorlauftemperatur":"vorlauf","ruecklauf":"ruecklauf","ruecklauftemperatur":"ruecklauf","spreizung":"spreizung","temperaturdifferenz":"spreizung"}.get(s)
    if previous in WEATHER_KEYS:
        if previous.startswith("regen"):
            return {"heute":"regenheute","morgen":"regenmorgen","uebermorgen":"regenuebermorgen","morgen frueh":"regenmorgenfrueh","heute abend":"regenabend","heute nacht":"regennacht"}.get(s)
        if previous.startswith("schnee"):
            return {"heute":"schneeheute","morgen":"schneemorgen"}.get(s)
        if previous in {"aktuell","heute","morgen","uebermorgen","kommendetage","abend","nacht","morgenfrueh","stunden"}:
            return {"heute":"heute","morgen":"morgen","uebermorgen":"uebermorgen","morgen frueh":"morgenfrueh","heute abend":"abend","heute nacht":"nacht","naechsten tage":"kommendetage","regen":"regenjetzt","wind":"wind","temperatur":"temperatur"}.get(s)
    if previous in WASTE:
        return {"restmuell":"restmuell","restabfall":"restmuell","biotonne":"bioabfall","biomuell":"bioabfall","papier":"papier","papiertonne":"papier","gelbe tonne":"wertstoff","wertstoffe":"wertstoff","morgen":"muell_morgen","heute":"muell_heute"}.get(s)
    if previous in {"solar","solarheute","prognose"}:
        return {"heute":"solarheute","morgen":"prognose","gerade":"solar","aktuell":"solar"}.get(s)
    if previous in {"netz","netzheute","einspeisungheute"}:
        return {"heute":"netzheute","gerade":"netz","aktuell":"netz","einspeisung heute":"einspeisungheute"}.get(s)
    if previous in {"preis","guenstig"}:
        return {"aktuell":"preis","jetzt":"preis","morgen am guenstigsten":"guenstig","guenstigster preis morgen":"guenstig"}.get(s)
    return None

class Followups:
    def __init__(self):self.context={}
    def clear(self,key):self.context.pop(key,None)
    def get(self,key,text):
        row=self.context.get(key)
        if not row:return None
        if row[0]<=monotonic():
            self.clear(key);return None
        return resolve(row[1],text)
    def remember(self,key,kind):
        self.context={k:v for k,v in self.context.items() if v[0]>monotonic()}
        if kind not in HEATING|WASTE|ENERGY|WEATHER_KEYS:
            self.clear(key);return
        if key not in self.context and len(self.context)>=50:self.context.pop(next(iter(self.context)))
        self.context[key]=(monotonic()+90,kind)
