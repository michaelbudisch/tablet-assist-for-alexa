"""One persistent, explicitly confirmed reminder; no private helpers."""
import asyncio
import re
from datetime import date, datetime, time, timedelta
from time import monotonic
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util
from .const import DOMAIN

NUM=dict(zip("null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn vierzehn fünfzehn sechzehn siebzehn achtzehn neunzehn zwanzig einundzwanzig zweiundzwanzig dreiundzwanzig".split(), range(24)))
NUM.update({"ein":1,"eine":1,"einen":1,"dreißig":30,"fünfundvierzig":45,"fünfzig":50})
YES={"ja","ja bitte","ja gerne","gerne","mach das","ja mach das","speichern","bestätigen"}
NO={"nein","nein danke","abbrechen","abbruch","stopp","stop","doch nicht","vergiss es"}
def num(v):return int(v) if v.isdecimal() else NUM.get(v,-1)
def parse_time(text,now,base=None):
    s=text.casefold().strip(" .?!")
    m=re.fullmatch(r"in (\d+|[a-zäöüß]+) (minuten?|stunden?|tagen?)",s)
    if m:
        n=num(m[1])*(1 if m[2].startswith("minute") else 60 if m[2].startswith("stunde") else 1440)
        return now+timedelta(minutes=n) if 0<n<=43200 else None
    m=re.fullmatch(r"(?:(heute|morgen|übermorgen|am \d{1,2}\.\d{1,2}\.(?:\d{4})?) )?um (\d{1,2}|[a-zäöüß]+)(?:(?::| uhr )(\d{1,2}|[a-zäöüß]+))?(?: uhr)?",s)
    if not m:return None
    day,h,mi=m.groups();h=num(h);mi=num(mi) if mi else 0
    if not (0<=h<24 and 0<=mi<60):return None
    d=base.date() if base else now.date()
    if day in ("heute","morgen","übermorgen"):d=now.date()+timedelta(days=("heute","morgen","übermorgen").index(day))
    elif day:
        try:
            parts=day[3:].split(".");d=date(int(parts[2]) if parts[2] else now.year,int(parts[1]),int(parts[0]))
        except (ValueError,IndexError):return None
    result=datetime.combine(d,time(h,mi),tzinfo=now.tzinfo)
    if result<=now and day is None and base is None:result+=timedelta(days=1)
    return result if now<result<=now+timedelta(days=366) else None

def when_text(when):
    return when.strftime("am %d.%m.%Y um %H:%M Uhr")

class Reminders:
    def __init__(self,hass,entry,cfg):
        self.hass=hass;self.cfg=cfg;self.store=Store(hass,1,f"{DOMAIN}.{entry.entry_id}.reminder")
        self.item=None;self.cancel_timer=None;self.lock=asyncio.Lock();self.pending={}
    async def load(self):
        data=await self.store.async_load()
        if isinstance(data,dict) and isinstance(data.get("message"),str) and data.get("when"):
            when=dt_util.parse_datetime(data["when"])
            if when and when.tzinfo:
                self.item=data
                if self.cfg.get('reminders_enabled'):self.arm(when)
    def close(self):
        if self.cancel_timer:self.cancel_timer();self.cancel_timer=None
        self.pending.clear()
    def arm(self,when):
        if self.cancel_timer:self.cancel_timer()
        self.cancel_timer=async_track_point_in_time(self.hass,self.deliver,max(when,dt_util.utcnow()+timedelta(seconds=1)))
    async def deliver(self,_now):
        async with self.lock:
            self.cancel_timer=None
            if not self.item:return
            item=self.item
            # Durable HA notification first; same ID is idempotent after restart.
            try:
                await self.hass.services.async_call("persistent_notification","create",{"title":"Tablet Assist – Erinnerung","message":item["message"],"notification_id":"tablet_assist_reminder"},blocking=True)
            except Exception:
                self.arm(dt_util.utcnow()+timedelta(minutes=5));return
            await self.store.async_save({})
            self.item=None
            # Do not broadcast stale reminders after a prolonged outage.
            when=dt_util.parse_datetime(item["when"])
            room=self.cfg.get("reminder_room")
            if room and room in self.cfg.get("rooms",{}) and (dt_util.utcnow()-when)<timedelta(minutes=15):
                try:await self.hass.services.async_call(DOMAIN,"announce",{"text":item["message"],"rooms":[room]},blocking=True)
                except Exception:pass
    def hold(self,key,item):
        self.pending={k:v for k,v in self.pending.items() if v["expiry"]>monotonic()}
        if len(self.pending)>=50:self.pending.pop(next(iter(self.pending)))
        item["expiry"]=monotonic()+60;self.pending[key]=item
    def offer(self,key,when,message,prefix="",pickup=None):
        if not self.cfg.get("reminders_enabled"):return prefix or "Erinnerungen sind nicht aktiviert.",False
        if self.item:return (prefix+" Es ist schon eine Erinnerung aktiv. Ich überschreibe sie nicht.").strip(),False
        self.hold(key,{"when":when,"message":message,"pickup":pickup})
        return (prefix+" Soll ich dich "+when_text(when)+" daran erinnern: "+message+"?").strip(),True
    async def handle(self,key,text,phrase):
        if not self.cfg.get("reminders_enabled"):return None
        now=dt_util.now()
        pending=self.pending.pop(key,None)
        if pending and pending["expiry"]>monotonic():
            if phrase in NO:return "In Ordnung, keine Erinnerung erstellt.",False
            if pending.get("stage")=="message":
                if re.match(r"^(?:wann|wie|was ist|welch|schalte|zeige|nenne)\b",phrase):return None
                if phrase in YES or not 0<len(text.strip())<=300:return "Bitte starte die Erinnerung erneut und nenne den Text.",False
                self.hold(key,{"stage":"time","message":text.strip()});return "Wann soll ich dich daran erinnern?",True
            if pending.get("stage")=="time":
                request=pending["day"]+" "+text if pending.get("day") and phrase.startswith("um ") else text
                when=parse_time(request,now)
                if when:return self.offer(key,when,pending["message"])
                if phrase in ("heute","morgen","übermorgen"):
                    pending["day"]=phrase;self.hold(key,pending);return "Um wie viel Uhr?",True
                if pending.get("day") and phrase.startswith("um "):
                    when=parse_time(pending["day"]+" "+text,now)
                    if when:return self.offer(key,when,pending["message"])
                return "Zeit nicht verstanden. Bitte starte die Erinnerung erneut.",False
            if phrase in YES and pending.get("stage")=="cancel":
                async with self.lock:
                    if not self.item or self.item["when"]!=pending["active_when"]:return "Die Erinnerung ist nicht mehr aktiv.",False
                    await self.store.async_save({})
                    self.item=None
                    if self.cancel_timer:self.cancel_timer();self.cancel_timer=None
                return "Die aktive Erinnerung wurde gelöscht.",False
            if phrase in YES:
                async with self.lock:
                    if self.item:return "Es ist bereits eine Erinnerung aktiv.",False
                    if pending["when"]<=now or (pending.get("pickup") and pending["when"].date()>=pending["pickup"]):return "Dieser Zeitpunkt ist nicht mehr gültig.",False
                    item={"message":pending["message"],"when":pending["when"].isoformat()}
                    await self.store.async_save(item);self.item=item;self.arm(pending["when"])
                return "Erinnerung "+when_text(pending["when"])+" gespeichert.",False
            request=re.sub(r"^(?:ja[,]? )?(?:lieber |stattdessen )?","",text.strip(),flags=re.I)
            if pending.get("when") and request.lower().startswith(("um ","heute ","morgen ","übermorgen ","am ","in ")):
                when=parse_time(request,now,pending["when"])
                if when and (not pending.get("pickup") or when.date()<pending["pickup"]):return self.offer(key,when,pending["message"],pickup=pending.get("pickup"))
                return "Dieser Zeitpunkt passt nicht. Bitte stelle die Anfrage erneut.",False
        if phrase in ("lösche meine erinnerung","loesche meine erinnerung","erinnerung löschen","erinnerung loeschen","lösche die erinnerung","entferne die erinnerung"):
            if not self.item:return "Es ist keine Erinnerung aktiv.",False
            self.hold(key,{"stage":"cancel","active_when":self.item["when"]})
            return "Soll ich die aktive Erinnerung löschen?",True
        if phrase in ("welche erinnerung ist aktiv","wann ist meine erinnerung","zeige meine erinnerung"):
            if not self.item:return "Es ist keine Erinnerung aktiv.",False
            return "Aktive Erinnerung: "+self.item["message"]+", "+when_text(dt_util.as_local(dt_util.parse_datetime(self.item["when"])))+".",False
        if phrase in ("erstelle eine erinnerung","erinnerung erstellen","erinnere mich","erinner mich","lege eine erinnerung an"):
            if self.item:return "Es ist bereits eine Erinnerung aktiv.",False
            self.hold(key,{"stage":"message"});return "Woran soll ich dich erinnern?",True
        m=re.fullmatch(r"(?:bitte )?erinner(?:e)? mich (.+?) (?:daran[, ]*|an |ans )(.+)",text.strip(" .?!"),re.I)
        if m:
            msg=m[2].strip(" ,.!?");when=parse_time(m[1],now)
            if not 0<len(msg)<=300:return "Bitte nenne eine kurze Erinnerungsnachricht.",False
            if when:return self.offer(key,when,msg)
            if m[1].casefold() in ("heute","morgen","übermorgen"):
                self.hold(key,{"stage":"time","day":m[1].casefold(),"message":msg});return "Um wie viel Uhr?",True
        m=re.fullmatch(r"(?:bitte )?erinner(?:e)? mich (?:daran[, ]*|an |ans )(.+)",text.strip(" .?!"),re.I)
        if m and 0<len(m[1])<=300:
            if self.item:return "Es ist bereits eine Erinnerung aktiv.",False
            self.hold(key,{"stage":"time","message":m[1]});return "Wann soll ich dich daran erinnern?",True
        return None
