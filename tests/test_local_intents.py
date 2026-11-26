"""Isolated tests: no Home Assistant install, household config or cloud accounts."""
import asyncio
import importlib
import sys
import types
import unittest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"custom_components/tablet_assist_for_alexa"
def module(name, **values):
    obj=types.ModuleType(name)
    obj.__dict__.update(values)
    sys.modules[name]=obj
    return obj

NOW=datetime(2026,11,21,18,0,tzinfo=timezone.utc)
def parse_datetime(s):
    try:return datetime.fromisoformat(s)
    except (ValueError,TypeError):return None

class Store:
    def __init__(self,*args):self.data=None
    async def async_load(self):return self.data
    async def async_save(self,data):self.data=dict(data)

module("homeassistant",__path__=[])
dt=module("homeassistant.util.dt",now=lambda:NOW,utcnow=lambda:NOW,as_local=lambda d:d,parse_datetime=parse_datetime)
module("homeassistant.util",__path__=[],dt=dt)
module("homeassistant.helpers",__path__=[])
module("homeassistant.helpers.storage",Store=Store)
module("homeassistant.helpers.event",async_track_point_in_time=lambda *a:lambda:None)
module("homeassistant.auth",__path__=[])
module("homeassistant.auth.permissions",__path__=[])
module("homeassistant.auth.permissions.const",POLICY_READ="read",POLICY_CONTROL="control")
module("tablet_test",__path__=[str(PACKAGE)])
intent=importlib.import_module("tablet_test.local_intents")
shop=importlib.import_module("tablet_test.shopping")
rem=importlib.import_module("tablet_test.reminders")
local=importlib.import_module("tablet_test.local_data")
weather=importlib.import_module("tablet_test.weather_data")
follow=importlib.import_module("tablet_test.followups")
learn=importlib.import_module("tablet_test.learning")
CTX=NS(user_id=None)

class Classifier(unittest.TestCase):
    def test_paraphrases(self):
        for q,expected in [
            ("Nenne mir die aktuelle Vorlauf Temperatur der Heizung.","vorlauf"),
            ("Was sagt der Heizungsrücklauf gerade?","ruecklauf"),
            ("Wie hoch ist die Spreizung?","spreizung"),
            ("Wie hoch ist mein Heizölbestand?","heizoel"),
            ("Wie viel Heizöl ist noch im Tank?","heizoel"),
            ("Wie viel Heizöl haben wir noch?","heizoel"),
            ("Wie teuer ist der Strom gerade?","preis"),
            ("Wann ist Strom morgen am günstigsten?","guenstig"),
            ("Wie viel Solarstrom haben wir heute produziert?","solarheute"),
            ("Was erzeugen wir gerade an PV-Leistung?","solar"),
            ("Wann wird der nächste Restmüller abgeholt?","restmuell"),
            ("Dann wird das nächste Mal Restmüll abgeholt.","restmuell"),
            ("Was haben wir aktuell auf der Bring-Einkaufsliste?","bring_list"),
            ("Welche Produkte stehen in unserer Einkaufsliste?","bring_list"),
            ("Wie wird das Wetter morgen früh?","morgenfrueh"),
            ("Brauche ich morgen einen Regenschirm?","regenmorgen"),
            ("Gibt es morgen Frost?","frost"),
            ("Wetter und Vorlauftemperatur","ambiguous"),
        ]:
            with self.subTest(q=q):self.assertEqual(intent.classify(q),expected)
    def test_do_not_guess(self):
        for q in ["Stelle die Vorlauftemperatur höher","Warum funktioniert meine Heizung nicht?","Was ist eine Wärmepumpe?","Wetter in London","Wie war das Wetter gestern?","Füge Milch zur Einkaufsliste hinzu","Wer war Albert Einstein?"]:
            with self.subTest(q=q):self.assertIsNone(intent.classify(q))

    def test_explicit_shopping_grammar(self):
        self.assertEqual(shop.parse_shopping("Setze Milch auf die Einkaufsliste."),("add","Milch"))
        self.assertEqual(shop.parse_shopping("Füge Brot zu Bring hinzu."),("add","Brot"))
        self.assertEqual(shop.parse_shopping("Streiche Butter von der Bring-Einkaufsliste."),("remove","Butter"))
        self.assertEqual(shop.parse_shopping("Steht Milch schon auf der Einkaufsliste?"),("check","Milch"))
        self.assertEqual(shop.parse_shopping("Lösche alles von der Einkaufsliste."),("invalid",""))
        self.assertEqual(shop.parse_shopping("Setze Milch und Brot auf Bring."),("invalid",""))
        self.assertIsNone(shop.parse_shopping("Setze Milch nicht auf die Einkaufsliste."))
        self.assertEqual(shop.exact_matches([{"summary":"Hafermilch"},{"summary":"Milch"}],"milch"),[{"summary":"Milch"}])

    def test_dates(self):
        st=NS(state="2",attributes={"2026-11-23":"Rest","2026-11-20":"old","not_a_date":1})
        self.assertEqual(local.collection_dates(st,NOW.date()),[date(2026,11,23)])
        self.assertEqual(local.collection_dates(NS(state="2026-12-03",attributes={}),NOW.date()),[date(2026,12,3)])

    def test_time(self):
        self.assertEqual(rem.parse_time("morgen um 18 Uhr",NOW),NOW+timedelta(days=1))
        self.assertEqual(rem.parse_time("in zwei Stunden",NOW),NOW+timedelta(hours=2))
        self.assertIsNone(rem.parse_time("heute um 12 Uhr",NOW))

class Operations(unittest.IsolatedAsyncioTestCase):
    async def test_shopping_mutations(self):
        rows=[];calls=[]
        async def service(domain,action,data,**kwargs):
            calls.append(action)
            self.assertEqual(data["entity_id"],"todo.example")
            if action=="get_items":return {"todo.example":{"items":[dict(i) for i in rows]}}
            if action=="add_item":rows.append({"summary":data["item"],"uid":"test-1"})
            elif action=="remove_item":rows[:]=[x for x in rows if x["uid"]!=data["item"]]
        hass=NS(services=NS(async_call=service))
        await shop.shopping(hass,"todo.example","add","Milch",CTX)
        await shop.shopping(hass,"todo.example","add","milch",CTX)
        self.assertEqual(calls.count("add_item"),1)
        self.assertIn("Milch",await shop.shopping(hass,"todo.example","list","",CTX))
        await shop.shopping(hass,"todo.example","remove","Hafermilch",CTX)
        self.assertEqual(calls.count("remove_item"),0)
        await shop.shopping(hass,"todo.example","remove","Milch",CTX)
        self.assertFalse(rows)

    async def test_unconfigured_and_permission(self):
        hass=NS(auth=NS(async_get_user=AsyncMock(return_value=NS(permissions=NS(check_entity=lambda *a:False)))),states={},services=NS(async_call=AsyncMock()))
        reader=local.LocalData(hass,{},None)
        result=await reader.handle("key","Wie hoch ist die Vorlauftemperatur?",CTX)
        self.assertIn("Keine Datenquelle",result[0])
        reader=local.LocalData(hass,{"sources":{"shopping":"todo.example"}},None)
        result=await reader.handle("key","Setze Milch auf die Einkaufsliste.",NS(user_id="example-user"))
        self.assertIn("nicht erlaubt",result[0])
        hass.services.async_call.assert_not_awaited()

    async def test_reminder_confirmation(self):
        hass=NS(services=NS(async_call=AsyncMock()))
        r=rem.Reminders(hass,NS(entry_id="example"),{"reminders_enabled":True})
        self.assertTrue(r.offer("a",NOW+timedelta(hours=1),"Test")[1])
        self.assertIsNone(r.item)
        self.assertIsNone(await r.handle("different","Ja","ja"))
        self.assertIsNone(r.item)
        answer=await r.handle("a","Ja","ja")
        self.assertIn("gespeichert",answer[0]);self.assertEqual(r.store.data["message"],"Test")
        self.assertFalse(r.offer("b",NOW+timedelta(hours=2),"Other")[1])
        self.assertEqual(r.item["message"],"Test")
        await r.deliver(NOW)
        self.assertIsNone(r.item)
        self.assertEqual(hass.services.async_call.call_args.args[:2],("persistent_notification","create"))

    async def test_waste_and_weather(self):
        cfg={"sources":{"restmuell":"sensor.example_date","weather":"weather.example"},"reminders_enabled":True}
        states={"sensor.example_date":NS(state="2026-11-23",attributes={}),"weather.example":NS(state="rainy",attributes={"temperature":4,"temperature_unit":"°C","precipitation_unit":"mm"})}
        hass=NS(states=states,services=NS(async_call=AsyncMock(return_value={"weather.example":{"forecast":[{"datetime":"2026-11-22T12:00:00+00:00","condition":"cloudy","temperature":5,"templow":-1}]}})))
        r=rem.Reminders(hass,NS(entry_id="x"),cfg)
        d=local.LocalData(hass,cfg,r)
        msg,keep=await d.handle("a","Wann wird Restmüll abgeholt?",CTX)
        self.assertTrue(keep);self.assertIn("23.11.2026",msg);self.assertIsNone(r.item)
        msg,keep=await d.handle("b","Wie wird das Wetter morgen?",CTX)
        self.assertIn("bewölkt",msg)

class ContextAndLearning(unittest.IsolatedAsyncioTestCase):
    def test_followups(self):
        self.assertEqual(follow.resolve("vorlauf","Und der Rücklauf?"),"ruecklauf")
        self.assertEqual(follow.resolve("aktuell","Und morgen?"),"morgen")
        self.assertEqual(follow.resolve("regenheute","Und morgen früh?"),"regenmorgenfrueh")
        self.assertEqual(follow.resolve("solarheute","Und morgen?"),"prognose")
        self.assertIsNone(follow.resolve("preis","Und morgen?"))
        self.assertIsNone(follow.resolve("vorlauf","Erhöhe die Temperatur"))
        c=follow.Followups();c.remember("a","vorlauf")
        self.assertIsNone(c.get("b","Und der Rücklauf?"))
        self.assertEqual(c.get("a","Und der Rücklauf?"),"ruecklauf")
        c.context["a"]=(0,"vorlauf")
        self.assertIsNone(c.get("a","Und der Rücklauf?"))

    async def test_approval(self):
        text="wir haben welche artikel auf der einkaufsliste"
        self.assertIsNone(intent.classify(text))
        self.assertEqual(learn.safe_phrase(text),text)
        r=learn.Learning(None,NS(entry_id="test"),{})
        r.observe(text);self.assertFalse(r.snapshot()["candidates"])
        with self.assertRaises(ValueError):await r.edit("approve",text,"bring_list")
        r.enabled=True;r.observe(text);r.observe(text)
        self.assertEqual(r.snapshot()["candidates"][text],2)
        self.assertIsNone(r.lookup(text))
        for phrase in ["mein passwort ist solarstrom","schalte die heizung aus","einkaufsliste Beispielname","strompreis 1234","mail@example.org wetter"]:
            self.assertIsNone(learn.safe_phrase(phrase));r.observe(phrase)
        self.assertEqual(len(r.snapshot()["candidates"]),1)
        with self.assertRaises(ValueError):await r.edit("approve",text,"todo.add_item")
        await r.edit("approve",text,"bring_list")
        self.assertEqual(r.lookup(text),"bring_list")
        self.assertFalse(r.snapshot()["candidates"])
        r.aliases={};await r.load();self.assertEqual(r.lookup(text),"bring_list")
        r.enabled=False;self.assertIsNone(r.lookup(text))
        await r.edit("clear");self.assertFalse(r.snapshot()["aliases"])
        self.assertEqual(r.store.data,{})

    async def test_followup_reads(self):
        hass=NS(states={"sensor.example_flow":NS(state="40",attributes={"unit_of_measurement":"°C"}),"sensor.example_return":NS(state="36",attributes={"unit_of_measurement":"°C"})})
        reader=local.LocalData(hass,{"sources":{"vorlauf":"sensor.example_flow","ruecklauf":"sensor.example_return"}},None)
        self.assertIn("40", (await reader.handle("a","Wie hoch ist die Vorlauftemperatur?",CTX))[0])
        self.assertIn("36", (await reader.handle("a","Und der Rücklauf?",CTX))[0])

if __name__=="__main__":unittest.main()
