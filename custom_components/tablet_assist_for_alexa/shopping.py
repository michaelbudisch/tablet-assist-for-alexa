"""Explicit shopping commands, exact matching, never bulk deletion."""
import re
import unicodedata

LIST = r"(?:bring[\s-]*(?:einkaufsliste|liste|app)|einkaufs[\s-]*(?:liste|zettel)|bring)"
DEST = r"(?:(?:auf|in|von|aus|bei|zu)\s+(?:(?:die|der|meine|meiner|unsere|unserer)\s+)?|zur\s+)"
POLITE = r"(?:(?:hey\s+)?jarvis[,\s]+|bitte\s+|(?:kannst|könntest)\s+du\s+(?:mir\s+)?(?:bitte\s+)?)?"
MUTATIONS = (
    ("add", r"(?:setz(?:e)?|schreib(?:e)?|pack(?:e)?|trag(?:e)?|füg(?:e)?)\s+(?:mir\s+)?(?:bitte\s+)?(?P<item>.+?)\s+"+DEST+LIST+r"(?:\s+(?:hinzu|ein|drauf))?"),
    ("remove",r"(?:entfern(?:e)?|lösch(?:e)?|streich(?:e)?|nimm)\s+(?:bitte\s+)?(?P<item>.+?)\s+"+DEST+LIST+r"(?:\s+(?:raus|runter|herunter))?"),
    ("add",r"(?P<item>.+?)\s+"+DEST+LIST+r"\s+(?:hinzufügen|setzen|schreiben|packen|eintragen)"),
    ("remove",r"(?P<item>.+?)\s+"+DEST+LIST+r"\s+(?:entfernen|löschen|streichen)"),
    ("check",r"(?:steht|ist)\s+(?P<item>.+?)\s+(?:(?:schon|bereits|noch)\s+)?"+DEST+LIST+r"(?:\s+(?:drauf|drin|eingetragen))?"),
    ("check",r"(?:haben wir|habe ich)\s+(?P<item>.+?)\s+(?:(?:schon|bereits|noch)\s+)?"+DEST+LIST+r"(?:\s+(?:stehen|drauf|drin))?"),
)
def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

def parse_shopping(text):
    value=text.strip(" \t\r\n.?!")
    if len(value)>250:return None
    if re.search(r'\b(?:nicht|keine|keinen|niemals)\b',value,re.I):return None
    for action,pattern in MUTATIONS:
        m=re.fullmatch(POLITE+pattern,value,re.I)
        if m:
            item=m["item"].strip(" ,.!?")
            # One explicit item, no ambiguous negation, bulk or multi-command phrases.
            if not 0<len(item)<=100 or re.search(r"\b(?:alles|alle|sämtliche|komplette|gesamte|ganze|nicht|und|oder|danach)\b|[,;]",item,re.I):
                return ("invalid", "")
            return action,item
    if re.fullmatch(POLITE+r"(?:was (?:muss|müssen|soll|sollen) (?:ich|wir) (?:noch )?(?:kaufen|einkaufen|besorgen)|was brauchen wir noch zum einkaufen)",value,re.I):
        return "list",""
    return None

def exact_matches(items, name):
    return [i for i in items if isinstance(i.get("summary"),str) and normalized(i["summary"])==normalized(name)]

async def shopping(hass, entity, operation, name, context):
    async def items():
        data=await hass.services.async_call("todo","get_items",{"entity_id":entity,"status":["needs_action"]},blocking=True,return_response=True,context=context)
        result=data[entity]["items"]
        if not isinstance(result,list):raise ValueError("Invalid todo response")
        return result
    if operation=="invalid":return "Bitte nenne genau einen Artikel, ohne Verneinung oder weitere Befehle."
    before=await items()
    hits=exact_matches(before,name)
    if operation=="list":
        if not before:return "Deine Einkaufsliste ist leer."
        n=len(before)
        labels=[str(i["summary"]) + (" ("+str(i["description"])+")" if i.get("description") else "") for i in before[:25]]
        return f"Auf deiner Einkaufsliste {'steht' if n==1 else 'stehen'} {n} Artikel: "+", ".join(labels)+("." if n<=25 else f". Und {n-25} weitere.")
    if operation=="check":return (f"{hits[0]['summary']} steht auf deiner offenen Einkaufsliste." if hits else f"{name} steht nicht auf deiner offenen Einkaufsliste.")
    if operation=="add":
        if hits:return f"{hits[0]['summary']} steht bereits auf deiner Einkaufsliste."
        await hass.services.async_call("todo","add_item",{"entity_id":entity,"item":name},blocking=True,context=context)
        return f"{name} wurde hinzugefügt." if exact_matches(await items(),name) else "Ich konnte das Hinzufügen nicht bestätigen. Bitte prüfe die Liste."
    if operation=="remove":
        if not hits:return f"{name} steht nicht auf deiner offenen Einkaufsliste. Ich habe nichts entfernt."
        if len(hits)!=1 or not hits[0].get("uid"):return "Der Artikel ist nicht eindeutig. Bitte prüfe die Liste."
        uid=hits[0]["uid"]
        await hass.services.async_call("todo","remove_item",{"entity_id":entity,"item":uid},blocking=True,context=context)
        return f"{hits[0]['summary']} wurde entfernt." if not any(i.get("uid")==uid for i in await items()) else "Ich konnte das Entfernen nicht bestätigen. Bitte prüfe die Liste."
    raise ValueError("Unknown shopping operation")
