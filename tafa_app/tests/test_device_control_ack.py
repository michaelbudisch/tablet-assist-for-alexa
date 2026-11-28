"""Regression tests for revision-based native microphone acknowledgment.

HA-specific runtime modules are not installed in this standalone unit-test
environment; compile the actual WakeDevices class with tiny mocked adapters.
"""
import ast
import asyncio
import re
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/"custom_components/tablet_assist_for_alexa/relay/relay_wake_devices.py"
SOURCE=PATH.read_text(encoding="utf-8")


class Owner:
    def __init__(self,id="owner",admin=False):
        self.id=id
        self.is_admin=admin
        self.is_active=True


class Store:
    def __init__(self):self.writes=[]
    async def async_save(self, value):self.writes.append(value)


class Hass:
    def __init__(self):
        self.signals=[]
        self.fired=[]
        self.bus=self

    def async_fire(self, kind, payload):
        self.fired.append((kind, payload))


def load_controller():
    tree=ast.parse(SOURCE)
    node=next(n for n in tree.body
              if isinstance(n,ast.ClassDef) and n.name=="WakeDevices")
    assignments={name:ast.literal_eval(item.value) for item in tree.body
                 if isinstance(item,ast.Assign) for target in item.targets
                 if isinstance(target,ast.Name) for name in [target.id]
                 if name in ("DEFAULTS","VALID","TELEMETRY")}
    namespace={
        **assignments,
        "asyncio":asyncio,
        "time":time,
        "SIGNAL":"changed",
        "SETTINGS_SIGNAL":"settings",
        "REGISTERED_SIGNAL":"registered",
        "REMOVED_SIGNAL":"removed",
        "DEVICE_ID":re.compile("^[a-f0-9]{32}$"),
        "WAKEWORDS":{"Hey Jarvis","Jarvis","Alexa"},
        "CHOICES":{"Hey Jarvis","Jarvis","Alexa","Alle drei"},
        "async_dispatcher_send":lambda hass,kind,id: hass.signals.append((kind,id)),
    }
    logic_path=ROOT/"custom_components/tablet_assist_for_alexa/switch_notice_logic.py"
    logic_tree=ast.parse(logic_path.read_text(encoding="utf-8"))
    reported_wake=next(n for n in logic_tree.body if isinstance(n,ast.FunctionDef)
                       and n.name=="reported_native_wake")
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[reported_wake],type_ignores=[])),str(logic_path),"exec"),namespace)
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[node],type_ignores=[])),str(PATH),"exec"),namespace)
    return namespace["WakeDevices"]


class AckTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.id="a"*32
        self.hass=Hass()
        self.store=Store()
        defaults={
            "device_id":self.id,"user_id":"owner","room":"Büro",
            "muted":False,"voice_mode":"wake","followup_limit":-1,
        }
        self.controller=load_controller()(self.hass,self.store,{self.id:defaults})
        self.user=Owner()

    async def test_set_value_produces_scoped_revision_and_ack_latency(self):
        await self.controller.set_value(self.id,"voice_mode","continuous")
        c=self.controller
        self.assertEqual(c.revisions[self.id],1)
        self.assertEqual(c.public(c.devices[self.id])["revision"],1)
        self.assertTrue(c.public(c.devices[self.id])["control"]["pending"])
        answer=await c.handle(self.user,"ack",self.id,
            {"revision":1,"channel":"websocket"})
        self.assertTrue(answer["accepted"])
        metrics=c.public(c.devices[self.id])["control"]
        self.assertFalse(metrics["pending"])
        self.assertEqual(metrics["ack_revision"],1)
        self.assertEqual(metrics["channel"],"websocket")
        self.assertGreaterEqual(metrics["latency_ms"],0)
        self.assertGreater(metrics["applied_at"],0)

    async def test_stale_ack_cannot_clear_new_pending_command(self):
        c=self.controller
        await c.set_value(self.id,"muted",True)
        await c.set_value(self.id,"muted",False)
        result=await c.handle(self.user,"ack",self.id,
            {"revision":1,"channel":"websocket"})
        self.assertFalse(result["accepted"])
        self.assertTrue(c.public(c.devices[self.id])["control"]["pending"])
        result=await c.handle(self.user,"ack",self.id,
            {"revision":2,"channel":"poll"})
        self.assertTrue(result["accepted"])
        self.assertEqual(c.public(c.devices[self.id])["control"]["channel"],"poll")

    async def test_reporting_does_not_trigger_control_push(self):
        c=self.controller
        await c.set_value(self.id,"voice_mode","wake")
        before=sum(1 for kind,_ in self.hass.signals if kind=="settings")
        ack=await c.handle(self.user,"ack",self.id,{"revision":1,"channel":"websocket"})
        self.assertTrue(ack["accepted"])
        report=await c.handle(self.user,"report",self.id,{"telemetry":{
            "wake_status":"listening: hey_jarvis","microphone":"wakeword",
            "audio":"ready","bluetooth":"connected","display":"android_managed",
            "battery":80,"app_version":"1.2.3","control_channel":"websocket",
            "local_followup_limit":-1}})
        self.assertTrue(report["accepted"])
        self.assertEqual(before,sum(1 for kind,_ in self.hass.signals if kind=="settings"))
        pub=c.public(c.devices[self.id])
        self.assertEqual(pub["telemetry"]["local_followup_limit"],-1)
        self.assertEqual(pub["control"]["ack_revision"],1)

    async def test_native_wake_report_routes_once_without_control_push(self):
        c=self.controller
        c.devices[self.id]["word"]="Jarvis"
        before=sum(kind=="settings" for kind,_ in self.hass.signals)
        for status in ("listening: jarvis", "detected: Jarvis", "detected: Jarvis"):
            result=await c.handle(self.user,"report",self.id,{
                "telemetry":{"wake_status":status}})
            self.assertTrue(result["accepted"])
        wake_events=[payload for kind,payload in self.hass.fired
                     if kind=="tafa_android_wakeword_routed"]
        self.assertEqual(len(wake_events),1)
        self.assertEqual(wake_events[0]["device_id"],self.id)
        self.assertEqual(wake_events[0]["wakeword"],"Jarvis")
        self.assertEqual(before,sum(kind=="settings" for kind,_ in self.hass.signals))

    async def test_denied_cross_owner_and_invalid_ack(self):
        c=self.controller
        with self.assertRaises(PermissionError):
            await c.handle(Owner("different"),"ack",self.id,
                {"revision":0,"channel":"websocket"})
        for invalid in ({"revision":True,"channel":"poll"},
                        {"revision":0,"channel":"fake"},
                        {"revision":-1,"channel":"websocket"}):
            with self.assertRaises(ValueError):
                await c.handle(self.user,"ack",self.id,invalid)

    async def test_followup_configuration_is_not_reset_by_ack(self):
        c=self.controller
        await c.handle(self.user,"configure",self.id,{"settings":{"followup_limit":10}})
        rev=c.revisions[self.id]
        await c.handle(self.user,"ack",self.id,{"revision":rev,"channel":"websocket"})
        self.assertEqual(c.devices[self.id]["followup_limit"],10)
        self.assertEqual(c.public(c.devices[self.id])["followup_limit"],10)


if __name__=="__main__":unittest.main()
