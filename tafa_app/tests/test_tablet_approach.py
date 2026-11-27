"""Controller contract: ownership, independent motion/wake state and stale presence."""
import unittest
from unittest.mock import patch
from test_device_control_ack import load_controller, Owner, Store, Hass

class ApproachTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.id="a"*32;self.store=Store();self.hass=Hass();self.user=Owner()
        self.c=load_controller()(self.hass,self.store,{self.id:{
            "device_id":self.id,"user_id":"owner","room":"Office"}})
    async def submit(self,**changes):
        value={"near":True,"face_percent":30,"threshold_percent":25};value.update(changes)
        return await self.c.handle(self.user,"approach",self.id,{"reading":value})
    async def test_presence_is_volatile_and_does_not_change_wake(self):
        self.c.telemetry[self.id]={"wake_status":"listening: hey_jarvis","last_wake":123}
        self.assertTrue((await self.submit())["accepted"])
        self.assertTrue(self.c.fresh_approach(self.id)["near"])
        self.assertEqual(self.c.telemetry[self.id]["last_wake"],123)
        self.assertEqual(self.c.telemetry[self.id]["wake_status"],"listening: hey_jarvis")
        self.assertEqual(self.store.writes,[])
    async def test_other_user_cannot_report_for_tablet(self):
        self.user=Owner("other")
        with self.assertRaises(PermissionError):await self.submit()
        self.assertFalse(self.c.approach)
    async def test_unknown_installation_cannot_report(self):
        self.id="b"*32
        with self.assertRaises(KeyError):await self.submit()
    async def test_disabled_or_error_is_unknown_not_absent(self):
        await self.submit(near=None,face_percent=None)
        self.assertIsNone(self.c.fresh_approach(self.id)["near"])
    async def test_stale_reading_expires_once(self):
        with patch("time.monotonic",return_value=100):await self.submit()
        with patch("time.monotonic",return_value=108.1):
            self.assertIsNone(self.c.fresh_approach(self.id))
            self.c.expire_approach();count=len(self.hass.signals);self.c.expire_approach()
            self.assertFalse(self.c.approach);self.assertEqual(len(self.hass.signals),count)
    async def test_reject_invalid_metadata_without_overwriting_previous(self):
        await self.submit()
        for changes in ({"near":1},{"face_percent":True},{"face_percent":101},{"threshold_percent":False},{"threshold_percent":1},{"face_percent":None}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):await self.submit(**changes)
        with self.assertRaises(ValueError):
            await self.c.handle(self.user,"approach",self.id,{"reading":{"near":True,"identity":"person"}})
        self.assertEqual(self.c.fresh_approach(self.id)["face_percent"],30)
