"""Only configured, allowlisted data sources; no inferred household mappings."""
import asyncio
from datetime import date, datetime, time, timedelta
import re
from homeassistant.util import dt as dt_util
from homeassistant.auth.permissions.const import POLICY_READ, POLICY_CONTROL
from .sources import METRICS, UNITS, WASTE_LABELS
from .web_search import SEARCH_PATTERN, FOLLOW_PATTERN, NUMBERS, query_searxng
from time import monotonic
from .local_intents import classify, WASTE_KEYS, has, normalize
from .weather_data import weather, numeric, WEATHER_KEYS
from .shopping import shopping, parse_shopping
from .followups import Followups

async def permitted(hass,entity,context,write=False):
    # HA's trusted device pipelines can have no user_id; only explicit configured sources are reachable.
    if context.user_id is None:return True
    user=await hass.auth.async_get_user(context.user_id)
    return bool(user and user.permissions.check_entity(entity,POLICY_CONTROL if write else POLICY_READ))

def collection_dates(state,today):
    if not state or state.state in ("unknown","unavailable"):return []
    dates=set()
    for raw in [state.state,*state.attributes]:
        if isinstance(raw,str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}",raw):
            try:
                d=date.fromisoformat(raw)
                if d>=today:dates.add(d)
            except ValueError:pass
    return sorted(dates)

class LocalData:
    def __init__(self,hass,cfg,reminders,learning=None):
        self.learning=learning;self.followups=Followups()
        self.hass=hass;self.cfg=cfg;self.reminders=reminders;self.sources=cfg.get("sources",{});self.shop_lock=asyncio.Lock();self.search_sessions={}

    async def source(self,key,context,write=False):
        entity=self.sources.get(key)
        if entity and await permitted(self.hass,entity,context,write):return entity
        return None

    async def waste(self,key,kind,context):
        now=dt_util.now();rows=[];missing=[]
        for source,label in WASTE_LABELS.items():
            if kind in WASTE_LABELS and source!=kind:continue
            entity=await self.source(source,context)
            if not entity:
                if kind==source:missing.append(label)
                continue
            dates=collection_dates(self.hass.states.get(entity),now.date())
            if dates:rows.append((dates[0],label))
            else:missing.append(label)
        rows.sort()
        if kind in ("muell_heute","muell_morgen"):
            d=now.date()+timedelta(days=int(kind=="muell_morgen"))
            rows=[r for r in rows if r[0]==d]
        if not rows:return ("Keine bestätigte Müllabholung für die konfigurierten Datenquellen in diesem Zeitraum." if not missing else "Es fehlen bestätigte Termine für "+", ".join(missing)+"."),False
        first=rows[0][0]; labels=" und ".join(l for d,l in rows if d==first)
        prefix="Die nächste passende Abholung: "+labels+" am "+first.strftime("%d.%m.%Y")+"."
        if kind=="muell_uebersicht":prefix="Nächste Abholtermine: "+"; ".join(l+" am "+d.strftime("%d.%m.%Y") for d,l in rows)+"."
        if missing:prefix+=" Für "+", ".join(missing)+" fehlen Termine."
        if first<=now.date() or not self.cfg.get("reminders_enabled"):return prefix,False
        when=datetime.combine(first-timedelta(days=1),time(18),tzinfo=now.tzinfo)
        if when<=now:when=now+timedelta(minutes=5)
        if when.date()>=first:return prefix,False
        return self.reminders.offer(key,when,labels+" rausstellen",prefix,pickup=first)

    async def metric(self,kind,context):
        entity=await self.source(kind,context)
        label,units=METRICS[kind]
        if not entity:return label+": Keine Datenquelle eingerichtet oder Zugriff nicht erlaubt."
        st=self.hass.states.get(entity)
        val=numeric(st.state) if st else None
        unit=st.attributes.get("unit_of_measurement") if st else None
        if val is None or unit not in units:return label+" ist nicht verfügbar oder die Einheit passt nicht."
        number=f"{val:.2f}".rstrip("0").rstrip(".").replace(".",",")
        if kind=="netz":
            return ("Wir beziehen "+number+" "+UNITS[unit]+" aus dem Stromnetz." if val>0 else "Wir speisen "+number.lstrip("-")+" "+UNITS[unit]+" ein." if val<0 else "Aktuell ist kein Netzbezug oder Export messbar.")
        if kind=="guenstig":
            ts=dt_util.parse_datetime(str(st.attributes.get("timestamp","")))
            if ts is None or ts.tzinfo is None or dt_util.as_local(ts).date()!=dt_util.now().date()+timedelta(days=1):return "Für morgen fehlt ein bestätigter Zeitstempel des günstigsten Strompreises."
            return label+": "+number+" "+UNITS[unit]+", um "+dt_util.as_local(ts).strftime("%H:%M")+" Uhr."
        result=label+": "+number+" "+UNITS[unit]+"."
        if kind in ("waschmaschine","waermepumpe"):result+=" Aus der Leistung allein lässt sich der Betriebszustand nicht sicher erkennen."
        return result

    def search_context(self, key):
        state = self.search_sessions.get(key)
        if state and state["expires"] > monotonic():
            return state
        self.search_sessions.pop(key, None)
        return None

    async def handle(self,key,text,context):
        # Native Android speech and dashboard typed queries share SearXNG.
        # A missing server is a normal optional-feature state.
        query = SEARCH_PATTERN.match(text.strip())
        if query:
            result = await query_searxng(self.hass, self.cfg.get("search_base", ""), query.group(1))
            self.search_sessions[key] = {"results": result["results"], "expires": monotonic() + 720}
            return result["message"], False
        follow = FOLLOW_PATTERN.match(text.strip())
        context_results = self.search_context(key)
        if follow and context_results:
            token = follow.group(1).lower()
            index = int(token) if token.isdigit() else NUMBERS.get(token, 0)
            matches = context_results.get("results", [])
            if index and index <= len(matches):
                item = matches[index-1]
                return "Treffer " + str(index) + ": " + item["title"] + ". Den Link kannst du in der TAFA-Infobox öffnen.", False
            return "Diese Treffer-Nummer gibt es in der letzten Suche nicht.", False
        request=parse_shopping(text)
        kind=None
        if request is None:
            kind=self.followups.get(key,text) or classify(text)
            if kind is None and self.learning:kind=self.learning.lookup(text)
        self.followups.clear(key)
        if kind not in (None,"ambiguous","bring_list"):self.followups.remember(key,kind)
        if kind is None and request is None and self.learning:self.learning.observe(text)
        if request is not None or kind=="bring_list":
            op,name=request or ("list","")
            entity=await self.source("shopping",context,op in ("add","remove"))
            if not entity:return "Die Einkaufsliste ist nicht eingerichtet oder der Zugriff ist nicht erlaubt.",False
            async with self.shop_lock:
                return await shopping(self.hass,entity,op,name,context),False
        if kind=="ambiguous":return "Ich habe mehrere Themen erkannt. Bitte frage nach einem Thema einzeln.",True
        if kind in WASTE_KEYS:return await self.waste(key,kind,context)
        if kind in WEATHER_KEYS:
            entity=await self.source("weather",context)
            if not entity:return "Die lokale Wetterquelle ist nicht eingerichtet oder der Zugriff ist nicht erlaubt.",False
            return await weather(self.hass,entity,kind,context),False
        s=normalize(text)
        if kind=="waschkosten" and not has(s,r'kost\w*|preis\w*|euro|cent'):kind="waschenergie"
        if kind=="wpheute" and has(s,r'kost\w*|preis\w*|euro|cent'):kind="wpkosten"
        if kind in METRICS:return await self.metric(kind,context),False
        return None
