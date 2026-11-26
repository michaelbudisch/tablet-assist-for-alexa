"""Conservative German read-only intent classifier; independent of HA and LLM."""
import re
import unicodedata

# Pure search phrase classifier; no optional HTTP/HA dependencies.
SEARCH_PATTERN = re.compile(
    r"^(?:(?:hey\s+)?(?:jarvis|tafa)[,\s]+)?(?:bitte\s+)?"
    r"(?:such(?:e)?|recherchier(?:e)?)\s+(?:(?:bitte|mal)\s+)*"
    r"(?:im\s+(?:internet|web)(?:\s+nach)?|online(?:\s+nach)?|nach)\s+(.{2,160})[.!?]?$", re.I)
FOLLOW_PATTERN = re.compile(r"^(?:oeffne|öffne|zeig(?:e)?)\s+(?:treffer\s+)?(?:nummer\s+)?([1-9]|zehn|eins|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun)\b", re.I)
NUMBERS = {"eins": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "fuenf": 5,
           "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10}


def normalize(text):
    s = unicodedata.normalize('NFKC', text).casefold().translate(str.maketrans({'ä':'ae','ö':'oe','ü':'ue','ß':'ss'}))
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    for pattern,value in ((r'\bvorlauf\s+(?:t\s+)?temperatur\b','vorlauftemperatur'),(r'\bruecklauf\s+temperatur\b','ruecklauftemperatur'),(r'\bheiz\s+oel\b','heizoel'),(r'\bp\s+v\b','pv'),(r'\brestmueller\b','restmuell'),(r'\bfoto\s*voltaik\b','photovoltaik')):
        s=re.sub(pattern,value,s)
    return re.sub(r'\s+',' ',s)

def has(s,pattern):
    return bool(re.search(r'\b(?:'+pattern+r')\b',s))

def classify(text):
    """Return read-only intent key; never dispatch actions."""
    s=normalize(text)
    s=re.sub(r'^(?:(?:hey )?(?:jarvis|jervis) |bitte |und )+','',s)
    # Common STT confusion at the beginning of collection-date questions only.
    if re.match(r'^dann (?:wird|werden)\b',s) and has(s,r'restmuell\w*|restabfall\w*|biomuell\w*|bioabfall\w*|altpapier\w*|gelbe tonne|muell\w*') and has(s,r'abgeholt|geholt|geleert'):
        s='wann'+s[4:]
    if not s or len(s)>280:return None
    if has(s,r'nicht|keine\w*|anschliessend|danach'):return None
    if has(s,r'schalt\w*|einschalt\w*|ausschalt\w*|aktiviere\w*|deaktiviere\w*|steuer\w*|regle\w*|erhoeh\w*|senk\w*|aender\w*|stell\w*|starte\w*|stoppe\w*|loesch\w*|erinner\w*|timer|wecker|durchsage|benachrichtig\w*|oeffne\w*|schliess\w*'):return None
    if has(s,r'funktionier\w*|bedeut\w*|definition|erklaer\w*|warum|weshalb|wieso|berechne\w*|formel|sollwert|optimal\w*|empfehl\w*|typisch\w*|normalwert\w*|einstell\w*|reparier\w*') or re.match(r'^(was ist ein(?:e|er)? |was sind )',s):return None
    query=bool(re.match(r'^(?:wie|was|wann|welch\w*|wieviel|wird|werden|ist|sind|hat|haben|laeuft|kommt|kostet|regnet|schneit|friert|gibt|brauche|muss|soll|nenne|nenn|sage|sag|zeige|zeig|gib|pruefe|ueberpruefe|kannst du|koenntest du|wuerdest du)\b',s))
    short=len(s.split())<=5 and not has(s,r'ich|du|wir|er|sie|es|soll|will|moechte')
    if not (query or short):return None
    # Flexible list reading only; mutations remain explicit HA sentence triggers.
    shopping=has(s,r'einkaufsliste\w*|einkaufs liste\w*|einkaufszettel\w*|bringeinkaufsliste\w*|bring (?:einkaufsliste|liste|app)')
    if shopping:
        if has(s,r'hinzufueg\w*|fueg\w*|schreib\w*|setz\w*|pack\w*|trag\w*|eintrag\w* hinzufuegen|entfern\w*|streich\w*|loesch\w*|nimm|kauf\w*|bestell\w*|erledig\w*|gestern|morgen|historisch\w*|andere\w* liste|nicht|statt|warum|wie funktioniert'):
            return None
        if re.match(r'^(?:ist|steht|haben wir|habe ich)\s+',s) and not re.match(r'^(?:ist|steht)\s+(?:die|meine|unsere)\s+',s):
            return None
        if re.match(r'^(?:was\b|welch\w* (?:artikel|produkte|eintraege|lebensmittel|sachen|dinge)\b|wie viel\w* (?:artikel|produkte|eintraege|sachen)\b|(?:lies|lese|zeig|zeige|nenne|nenn|sage|sag|pruefe|ueberpruefe)\b|(?:kannst|koenntest|wuerdest) du\b)',s) or short:
            return 'bring_list'
        return None
    today=has(s,r'heute|heutig\w*|seit mitternacht|bisher')
    tomorrow=has(s,r'morgen|morgig\w*')
    after=has(s,r'uebermorgen')
    if has(s,r'gestern|vorgestern|letzte\w* (?:woche|monat|jahr)|letzten \d+ tage|vergangen\w*|historisch\w*|naechste\w* (?:woche|monat|jahr)|in \d+ tagen|wochenende|montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag'):return None
    cost=has(s,r'kost\w*|preis\w*|strompreis\w*|stromkosten\w*|stromtarif\w*|teuer\w*|billig\w*|guenstig\w*|cent|euro')
    energy=has(s,r'verbrauch\w*|energie\w*|kilowattstunden?|kwh|kw h|ertrag\w*|erzeug\w*|produzier\w*|produkti\w*|bezog\w*|eingespeist')
    electric=has(s,r'strom\w*|watt|kilowatt\w*|kwh|leistung\w*|energie\w*')
    power=has(s,r'watt|kilowatt|leistung\w*')
    topics=[]
    for key,pat in (
        ('vorlauf',r'vorlauf\w*|heizungsvorlauf\w*'),
        ('ruecklauf',r'ruecklauf\w*|heizungsruecklauf\w*'),
        ('spreizung',r'spreizung|temperaturdifferenz|temperaturunterschied|differenz zwischen vorlauf und ruecklauf'),
        ('oil',r'heizoel\w*|oeltank\w*|heizoeltank\w*|oelbestand|oelverbrauch|tankfuellung|oel im tank|liter oel'),
        ('washer',r'waschmaschine\w*|waesche\w*|waschgang\w*|waschprogramm\w*'),
        ('hp',r'waermepumpe\w*'),
        ('fridge',r'kuehlschrank\w*'),
        ('solar',r'solar\w*|pv\w*|photovoltaik\w*|wechselrichter\w*'),
        ('grid',r'netzbezug\w*|netzverbrauch\w*|stromnetz|netzeinspeis\w*|einspeis\w*|eingespeist|aus dem netz|ins netz|vom netz')):
        if has(s,pat):topics.append(key)
    if has(s,r'strompreis\w*|stromkosten\w*|stromtarif\w*|strom|kilowattstunde') and cost and not any(x in topics for x in ('washer','hp','fridge','solar','grid')):topics.append('price')
    if has(s,r'restmuell\w*|restabfall\w*|biomuell\w*|bioabfall\w*|biotonne\w*|altpapier\w*|papiertonne\w*|blaue tonne|gelbe tonne|gelber sack|schwarze tonne|braune tonne|wertstoff\w*|plastikmuell\w*|muell\w*|abfall\w*') or (has(s,r'papier') and has(s,r'abhol\w*|abfuhr\w*|tonne\w*')):topics.append('waste')
    if has(s,r'wetter\w*|regen\w*|regnet\w*|regenschirm\w*|niederschlag\w*|schnee\w*|schnei\w*|frost\w*|friert|wind\w*|sturm\w*|luftdruck\w*|luftfeucht\w*|aussentemperatur\w*|gefuehlt\w*|draussen'):topics.append('weather')
    if 'spreizung' in topics and set(topics)<={'vorlauf','ruecklauf','spreizung'}:topics=['spreizung']
    if len(topics)>1:return 'ambiguous'
    if not topics:return None
    topic=topics[0]
    if topic in ('vorlauf','ruecklauf','spreizung'):
        return topic if not (tomorrow or after or cost or energy or has(s,r'durchschnitt\w*|maximum|minimum|hoechst\w*|niedrigst\w*')) else None
    if topic=='oil':
        if tomorrow or after or cost:return None
        return ('oelverbrauch' if today else None) if has(s,r'verbrauch\w*|verheiz\w*') else 'heizoel'
    if topic=='washer':
        if tomorrow or after or has(s,r'restlaufzeit|wie lange|wann fertig|welches programm|programmende'):return None
        return 'waschkosten' if today and (cost or energy) and not power else 'waschmaschine' if not cost and (power or not energy) else None
    if topic=='hp':
        if tomorrow or after:return None
        return 'wpheute' if today and (cost or energy) and not power else 'waermepumpe' if not cost and (power or not energy) else None
    if topic=='fridge':
        if tomorrow or after or cost:return None
        return 'kuehlschrankheute' if today and energy and not power else 'kuehlschrank' if power or (electric and not energy) else None
    if topic=='solar':
        if after or cost or (power and tomorrow) or (power and today and not has(s,r'gerade|aktuell|jetzt|momentan')) or (not today and not tomorrow and has(s,r'kilowattstunden?|kwh|kw h|ertrag\w*') and not power):return None
        return 'prognose' if tomorrow else 'solarheute' if today and not power else 'solar'
    if topic=='grid':
        if tomorrow or after or cost or (today and power) or (not today and has(s,r'kilowattstunden?|kwh|kw h')):return None
        return ('einspeisungheute' if has(s,r'einspeis\w*|eingespeist|ins netz') else 'netzheute') if today else 'netz' if not energy or electric else None
    if topic=='price':
        if after or has(s,r'stromkosten\w*|verbrauchskosten\w*|gesamtkosten\w*|insgesamt|rechnung\w*'):return None
        if tomorrow:return 'guenstig' if has(s,r'guenstig\w*|billig\w*|niedrig\w*|minimum') else None
        return 'preis' if not has(s,r'durchschnitt\w*|hoechst\w*|teuerst\w*|guenstigst\w*|billigst\w*') else None
    if topic=='waste':
        if query and not has(s,r'wann|abhol\w*|abfuhr\w*|geholt|geleert|kalender\w*|termin\w*|dran|rausstell\w*|tonne\w*|steht an|uebersicht|kommt'):return None
        if has(s,r'trenn\w*|entsorg\w*|recycl\w*|gebuehr\w*|kost\w*|sperrmuell|sondermuell') or after:return None
        kinds=[]
        for kind,pat in [('restmuell',r'restmuell\w*|restabfall\w*|schwarze tonne'),('bioabfall',r'biomuell\w*|bioabfall\w*|biotonne\w*|braune tonne'),('papier',r'papier\w*|altpapier\w*|blaue tonne'),('wertstoff',r'wertstoff\w*|gelbe tonne|gelber sack|plastikmuell\w*')]:
            if has(s,pat):kinds.append(kind)
        if len(kinds)>1:return None
        if kinds:return kinds[0] if not (today or tomorrow) else None
        if tomorrow:return 'muell_morgen'
        if today:return 'muell_heute'
        return 'muell_uebersicht' if has(s,r'kalender\w*|abfallkalender\w*|muellkalender\w*|alle|termine|uebersicht') else 'muell_naechste'
    if topic=='weather':
        if has(s,r'warn\w*|unwetter\w*|uv\w*|sonnenaufgang\w*|sonnenuntergang\w*|(?:wie viel|wieviel) sonne|pollen\w*|wo genau|wo regnet') or re.search(r'\b(?:in|fuer|bei)\s+(?!den\b|die\b|der\b|uns\b|zuhause\b|dieser\b|naehe\b|\d+\b|zwei\b|sechs\b|morgen\b|heute\b|uebermorgen\b|wetter\b|ein\b|eine\b)\w+',s):return None
        if re.search(r'\bin (?:der|den|dem) (?!nacht\b|naehe\b|naechsten\b|kommenden\b|fruehe\b|region hier\b)\w+',s):return None
        morning=tomorrow and has(s,r'frueh|vormittag\w*')
        evening=today and has(s,r'abend\w*')
        night=has(s,r'nacht\w*') and not tomorrow and not after
        if has(s,r'regenwahrscheinlichkeit|wahrscheinlich\w*|prozent') and has(s,r'regen\w*|regnet\w*'):return 'regenwahrscheinlichkeit'
        if has(s,r'frost\w*|friert|unter null|minusgrad\w*'):return 'frost' if tomorrow else None
        if has(s,r'schnee\w*|schnei\w*'):return None if after or morning or evening or night else 'schneemorgen' if tomorrow else 'schneeheute' if today else 'schnee'
        if has(s,r'regen\w*|regnet\w*|niederschlag\w*|regenschirm\w*'):
            if has(s,r'hoert\w*|aufhoer\w*|ende|trocken\w*|stundenlang|wie lange|den ganzen tag|wie viel niederschlag'):return None
            return 'regenuebermorgen' if after else 'regenmorgenfrueh' if morning else 'regenmorgen' if tomorrow else 'regenabend' if evening else 'regennacht' if night else 'regenheute' if today else 'regenzwei' if has(s,r'(?:zwei|2) stunden') else 'regennachher' if has(s,r'wann|spaeter|nachher|bald|naechste\w* stunden|stunden') else 'regenjetzt'
        if has(s,r'luftfeucht\w*|luftdruck\w*|wind\w*|sturm\w*|gefuehlt\w*'):
            if today or tomorrow or after or night:return None
            return 'feuchte' if has(s,r'luftfeucht\w*') else 'druck' if has(s,r'luftdruck\w*') else 'gefuehlt' if has(s,r'gefuehlt\w*') else 'wind'
        if morning:return 'morgenfrueh'
        if evening:return 'abend'
        if night:return 'nacht'
        if after:return 'uebermorgen'
        if tomorrow:return 'morgen'
        if today:return 'heute'
        if has(s,r'naechste\w* tage\w*|kommende\w* tage\w*'):return 'kommendetage'
        if has(s,r'naechste\w* stunden\w*|kommende\w* stunden\w*|nachher|spaeter'):return 'stunden'
        if has(s,r'temperatur\w*|aussentemperatur\w*|grad|warm|kalt'):return 'temperatur'
        return 'aktuell'
    return None

WASTE_KEYS = frozenset(('restmuell','bioabfall','papier','wertstoff','muell_naechste','muell_uebersicht','muell_heute','muell_morgen'))

