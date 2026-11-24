"""Isolated room frame stores; no physical cameras."""
import sys
import types
import unittest
from pathlib import Path
folder=Path(__file__).resolve().parents[1]/"custom_components"/"jarvis_tablet_audio"
pkg=types.ModuleType("room_fixture");pkg.__path__=[str(folder)];sys.modules[pkg.__name__]=pkg
from room_fixture.relay_room_camera_store import RoomCameraStore
from room_fixture.relay_room_audio import RoomAudioTransport

class RoomCameraTests(unittest.TestCase):
    def setUp(self):
        self.now=100
        self.t=RoomAudioTransport(lambda:self.now)
        self.t.provision("a","user_a")
        self.t.provision("b","user_b")
        self.t.settings={"a":{"camera_enabled":True},"b":{"camera_enabled":True}}
        self.s=RoomCameraStore(self.t,lambda:self.now)
        self.a="a"*32;self.b="b"*32
    def test_opt_in_and_isolation(self):
        _,a=self.s.register("user_a",self.a)
        _,b=self.s.register("user_b",self.b)
        self.s.put("user_a",self.a,a,1,b"a",1,True,1)
        self.s.put("user_b",self.b,b,1,b"b",1,False,10)
        self.assertEqual(self.s.frames["a"].image,b"a")
        self.assertEqual(self.s.frames["b"].image,b"b")
        with self.assertRaises(PermissionError):self.s.authorized("user_b",self.a,a)
        self.t.settings["a"]["camera_enabled"]=False
        self.assertIn("a",self.s.sync())
        self.assertFalse(self.s.fresh("a"))
        self.assertTrue(self.s.fresh("b"))
    def test_expiry_and_stop(self):
        _,a=self.s.register("user_a",self.a)
        self.s.put("user_a",self.a,a,1,b"a",1,True,2)
        self.now+=16
        self.assertIn("a",self.s.expire())
        self.assertFalse(self.s.fresh("a"))
        self.s.stop("user_a",self.a,a)
        with self.assertRaises(PermissionError):self.s.authorized("user_a",self.a,a)
    def test_revoke_and_pair(self):
        _,a=self.s.register("user_a",self.a)
        with self.assertRaises(RuntimeError):self.s.register("user_a",self.b)
        self.t.revoke("a")
        self.s.sync()
        self.assertNotIn("a",self.s.frames)
        with self.assertRaises(PermissionError):self.s.authorized("user_a",self.a,a)
    def test_limits(self):
        _,a=self.s.register("user_a",self.a)
        self.s.put("user_a",self.a,a,1,b"a",1,True,2)
        with self.assertRaises(RuntimeError):self.s.put("user_a",self.a,a,2,b"a",1,True,2)
        self.now+=1
        with self.assertRaises(ValueError):self.s.put("user_a",self.a,a,2,b"a",1,True,100)
    def test_disabled_by_default(self):
        self.t.settings["a"]={}
        with self.assertRaises(PermissionError):self.s.register("user_a",self.a)
