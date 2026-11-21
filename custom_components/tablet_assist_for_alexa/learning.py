"""Opt-in, admin-approved, read-only aliases. No audio or conversation history."""
import asyncio
import re
from time import time
from homeassistant.helpers.storage import Store
from .const import DOMAIN
from .local_intents import classify,normalize
from .sources import METRICS
from .weather_data import WEATHER_KEYS

# No shopping mutations, reminders, services, commands or waste reminder offers.
LEARNABLE=frozenset(METRICS)|frozenset(WEATHER_KEYS)|{"bring_list"}
# Only generic home-data words may be collected automatically. Unknown terms,
# names, numbers, addresses, dictation, private content are not captured.
SAFE_WORDS=frozenset(("hey jarvis jervis bitte und aktuell gerade momentan jetzt heute morgen uebermorgen "
    "am abend nacht frueh vormittag welche welcher welches was wie viel viele wann ist sind wird werden "
    "wir ich mir uns unser unsere unserer meinen meine meiner der die das den dem ein eine im in auf "
    "von fuer bei zu an aus es noch schon alles alle steht stehen haben hat sagt sag sage nenne nenn "
    "zeige zeig lies lese vor liesse kannst koenntest du sagen nennen anzeigen abfragen lesen vorlesen "
    "wetter wetterbericht wettervorhersage wetterprognose aussentemperatur temperatur grad warm kalt "
    "wind windstaerke windgeschwindigkeit luftfeuchtigkeit luftdruck regen regnet regnen niederschlag "
    "schnee schneit schneien frost sonnig sonne draussen vorlauf vorlauftemperatur heizungsvorlauf "
    "heizung heizungsruecklauf ruecklauf ruecklauftemperatur spreizung temperaturdifferenz "
    "solar solarstrom pv photovoltaik wechselrichter strom strompreis strompreise netz netzleistung "
    "netzbezug einspeisung leistung verbrauch erzeugt produziert ertrag watt kilowatt kilowattstunden "
    "heizoel oeltank tank fuellstand waermepumpe waschmaschine kuehlschrank einkaufsliste "
    "bringeinkaufsliste bring liste app einkaufszettel produkte artikel eintraege lebensmittel "
    "sachen dinge drauf drin eingetragen brauchen benoetigen kosten teuer guenstig guenstigsten "
    "wiehoch ungefaehr genau denn eigentlich aktuellster").split())
TOPIC_WORDS=frozenset(("wetter aussentemperatur vorlauf vorlauftemperatur heizungsvorlauf ruecklauf "
    "ruecklauftemperatur heizungsruecklauf spreizung strompreis strompreise solarstrom solar pv "
    "photovoltaik netzbezug netzleistung heizoel oeltank waermepumpe waschmaschine kuehlschrank "
    "einkaufsliste bringeinkaufsliste einkaufszettel bring regen schnee frost luftdruck wind").split())

def safe_phrase(text):
    if not re.fullmatch(r"[a-zA-ZäöüÄÖÜß ,.?!\t-]+",text):return None
    s=normalize(text)
    words=s.split()
    if len(s)>140 or not 2<=len(words)<=20 or not set(words)<=SAFE_WORDS or not set(words)&TOPIC_WORDS:
        return None
    if classify(s) is not None:return None
    return s

class Learning:
    def __init__(self,hass,entry,cfg):
        self.enabled=bool(cfg.get("learning_enabled",False))
        self.store=Store(hass,1,f"{DOMAIN}.{entry.entry_id}.aliases")
        self.aliases={};self.candidates={};self.lock=asyncio.Lock()
    async def load(self):
        data=await self.store.async_load()
        if isinstance(data,dict):
            self.aliases={k:v for k,v in data.items() if v in LEARNABLE and safe_phrase(k)==k}
    def lookup(self,text):
        if not self.enabled:return None
        return self.aliases.get(normalize(text))
    def prune(self):
        self.candidates={k:v for k,v in self.candidates.items() if v["time"]>time()-86400}
    def observe(self,text):
        if not self.enabled:return
        s=safe_phrase(text)
        if not s or s in self.aliases:return
        self.prune()
        if s not in self.candidates and len(self.candidates)>=30:self.candidates.pop(next(iter(self.candidates)))
        row=self.candidates.get(s,{"count":0})
        self.candidates[s]={"count":min(row["count"]+1,999),"time":time()}
    def snapshot(self):
        self.prune()
        return {"enabled":self.enabled,"aliases":self.aliases.copy(),"candidates":{k:v["count"] for k,v in self.candidates.items()},"targets":sorted(LEARNABLE)}
    async def edit(self,action,phrase="",target=""):
        async with self.lock:
            phrase=normalize(phrase)
            if action=="clear":
                await self.store.async_save({});self.aliases={};self.candidates.clear()
            elif action=="dismiss":
                self.candidates.pop(phrase,None)
            elif action=="delete":
                new=dict(self.aliases);new.pop(phrase,None)
                await self.store.async_save(new);self.aliases=new
            elif action=="approve":
                if not self.enabled or safe_phrase(phrase)!=phrase or target not in LEARNABLE:
                    raise ValueError("Only allowlisted generic read-only phrases can be approved.")
                if len(self.aliases)>=100 and phrase not in self.aliases:raise ValueError("Alias limit reached.")
                new={**self.aliases,phrase:target}
                await self.store.async_save(new);self.aliases=new;self.candidates.pop(phrase,None)
            else:raise ValueError("Unknown action")
        return self.snapshot()
