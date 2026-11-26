"""Isolated HA WebSocket subscription tests: authorization, scoped push, no tokens."""
import ast
import asyncio
import re
import types
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"custom_components/tablet_assist_for_alexa/device_settings_ws.py"
CONTROLLER=ROOT/"custom_components/tablet_assist_for_alexa/relay/relay_wake_devices.py"


class User:
    def __init__(self, uid, admin=False):
        self.id=uid
        self.is_active=True
        self.is_admin=admin


class Connection:
    def __init__(self,user):
        self.user=user
        self.subscriptions={}
        self.result=[]
        self.errors=[]
        self.events=[]
    def send_result(self, id, result):self.result.append((id,result))
    def send_error(self, id, code, message):self.errors.append((id,code,message))
    def send_event(self, id, event):self.events.append((id,event))


class TestDeviceSettingsWS(unittest.TestCase):
    def setUp(self):
        self.listeners=[]
        def connect(hass,signal,callback):
            self.listeners.append((signal,callback))
            return lambda: self.listeners.remove((signal,callback))
        tree=ast.parse(SOURCE.read_text())
        nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
               and n.name in ("settings_payload","device_settings_subscribe")]
        for node in nodes:node.decorator_list=[]
        namespace={"DOMAIN":"tablet_assist_for_alexa",
                   "KEY":"wake_devices_dynamic",
                   "SETTINGS_SIGNAL":"tablet_assist_for_alexa_tablet_settings_changed",
                   "async_dispatcher_connect":connect}
        exec(compile(ast.fix_missing_locations(
            ast.Module(body=nodes,type_ignores=[])),str(SOURCE),"exec"),namespace)
        self.subscribe=namespace["device_settings_subscribe"]
        self.payload=namespace["settings_payload"]
        self.a="a"*32
        self.b="b"*32
        self.devices={
            self.a:{"device_id":self.a,"user_id":"ownerA","muted":False,
                    "voice_mode":"wake","word":"Hey Jarvis","followup_limit":0,
                    "secret_token":"NEVER-EXPOSE"},
            self.b:{"device_id":self.b,"user_id":"ownerB","muted":True,
                    "voice_mode":"continuous","followup_limit":-1},
        }
        def allowed(user,device):
            return user.is_admin or user.id==device["user_id"]
        self.controller=types.SimpleNamespace(devices=self.devices,allowed=allowed,revisions={self.a:4,self.b:2})
        self.hass=types.SimpleNamespace(data={
            "tablet_assist_for_alexa":{"wake_devices_dynamic":self.controller}})

    def test_owner_gets_immediate_initial_state_and_targeted_updates(self):
        conn=Connection(User("ownerA"))
        asyncio.run(self.subscribe(self.hass,conn,{"id":23,"device_id":self.a}))
        self.assertTrue(conn.result[0][1]["subscribed"])
        self.assertEqual(conn.events[0][1]["device_id"],self.a)
        self.assertEqual(conn.events[0][1]["revision"],4)
        self.assertNotIn("secret_token",str(conn.events))
        self.assertNotIn("user_id",str(conn.events))
        self.devices[self.a]["muted"]=True
        self.listeners[0][1](self.b)
        self.assertEqual(len(conn.events),1)
        self.listeners[0][1](self.a)
        self.assertEqual(len(conn.events),2)
        self.assertTrue(conn.events[-1][1]["muted"])
        conn.subscriptions[23]()
        self.assertEqual(self.listeners,[])

    def test_other_user_cannot_subscribe(self):
        conn=Connection(User("ownerB"))
        asyncio.run(self.subscribe(self.hass,conn,{"id":3,"device_id":self.a}))
        self.assertEqual(conn.errors[0][1],"unauthorized")
        self.assertFalse(conn.events)
        self.assertFalse(self.listeners)

    def test_admin_access_and_revoked_ownership(self):
        conn=Connection(User("admin",admin=True))
        asyncio.run(self.subscribe(self.hass,conn,{"id":4,"device_id":self.a}))
        self.assertEqual(len(conn.events),1)
        self.devices[self.a]["voice_mode"]="continuous"
        self.listeners[0][1](self.a)
        self.assertEqual(conn.events[-1][1]["voice_mode"],"continuous")

    def test_telemetry_not_in_settings_push_path(self):
        source=CONTROLLER.read_text()
        self.assertIn('self.settings_changed(identifier)',source)
        self.assertIn('SETTINGS_SIGNAL',source)
        part=source.split('if action == "report":',1)[1].split('if action == "wake":',1)[0]
        self.assertNotIn('settings_changed(',part)


if __name__=="__main__":
    unittest.main()
