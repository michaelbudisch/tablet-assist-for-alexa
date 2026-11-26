"""Regression coverage for HA-admin WebSocket device/room management.

Compiles only the real standalone core coroutine from source, avoiding an
installed Home Assistant dependency in the TAFA App unit-test environment.
"""
import ast
import asyncio
import re
import types
import unittest
from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[2] /
          "custom_components/tablet_assist_for_alexa/device_admin_ws.py")


def load_action():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    method = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "perform_device_admin")
    namespace = {
        "DOMAIN": "tablet_assist_for_alexa",
        "DEVICE_ID": re.compile(r"[a-f0-9]{32}\Z"),
        "ROOM": re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z"),
        "cleanup_tablet": lambda hass, identifier: hass.cleaned_tablets.append(identifier),
        "cleanup_room": lambda hass, room: hass.cleaned_rooms.append(room),
    }
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=[method], type_ignores=[])), str(SOURCE), "exec"),
         namespace)
    return namespace["perform_device_admin"]


class User:
    def __init__(self, uid, name, admin=False, active=True, system=False):
        self.id, self.name = uid, name
        self.is_admin, self.is_active, self.system_generated = admin, active, system


class Auth:
    def __init__(self, users):
        self.users = {u.id: u for u in users}
    async def async_get_users(self):
        return list(self.users.values())
    async def async_get_user(self, user_id):
        return self.users.get(user_id)


class Fixture:
    def __init__(self):
        self.admin = User("admin", "Administrator", admin=True)
        self.user = User("tablet", "Tablet Benutzer")
        self.auth = Auth([self.admin, self.user,
                          User("inactive", "Inactive", active=False),
                          User("system", "System", system=True)])
        self.devices = {}
        self.controller = types.SimpleNamespace(
            lock=asyncio.Lock(), devices=self.devices,
            public=lambda d: dict(d),
            changed=lambda _: None)
        async def save_controller():
            return None
        async def handle(user, action, identifier, payload):
            if action == "delete":
                self.devices.pop(identifier)
                return {"removed": True}
            return {"device": {"device_id": identifier}}
        self.controller.save = save_controller
        self.controller.handle = handle
        rooms, settings = {}, {}
        def provision(room, principal):
            rooms[room] = principal
        def status(principal):
            room = next(r for r, uid in rooms.items() if uid == principal)
            return {"room": room, "online": False, "ready": False}
        self.sessions, self.jobs = {}, {}
        def revoke(room):
            rooms.pop(room, None)
            self.sessions.pop(room, None)
            for job in tuple(self.jobs):
                if self.jobs[job] == room:
                    self.jobs.pop(job)
        self.transport = types.SimpleNamespace(
            rooms=rooms, settings=settings,
            provision=provision, revoke=revoke, status=status)
        self.cleaned_tablets, self.cleaned_rooms = [], []
        self.saved = 0
        async def persist():
            self.saved += 1
        self.data = {"tablet_assist_for_alexa": {
            "wake_devices_dynamic": self.controller,
            "room_audio": self.transport,
            "room_audio_save": persist,
        }}


class DeviceAdminWebSocketTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = staticmethod(load_action())

    async def test_new_non_admin_user_appears_without_tablets(self):
        hass = Fixture()
        response = await self.action(hass, hass.admin, {"action": "list"})
        self.assertEqual(response["users"],
                         [{"id": "tablet", "name": "Tablet Benutzer"}])
        self.assertEqual(response["rooms"], [])
        self.assertEqual(response["devices"], [])
        self.assertNotIn("token", str(response))

    async def test_create_room_first_then_list_user_and_room(self):
        hass = Fixture()
        result = await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        self.assertTrue(result["created"])
        self.assertEqual(hass.saved, 1)
        view = await self.action(hass, hass.admin, {"action": "list"})
        self.assertEqual(view["rooms"][0]["room"], "buero")
        self.assertEqual(view["rooms"][0]["user_id"], "tablet")
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "create", "room": "buero", "user_id": "tablet"})


    async def test_explicit_camera_setup_reuses_enrolled_owner_without_transfer(self):
        hass = Fixture()
        did = "c" * 32
        hass.devices[did] = {"device_id": did, "room": "Büro", "user_id": "tablet"}
        with self.assertRaises(PermissionError):
            await self.action(hass, hass.user, {
                "action": "camera_setup", "room": "buero", "device_id": did})
        result = await self.action(hass, hass.admin, {
            "action": "camera_setup", "room": "buero", "device_id": did})
        self.assertEqual(result, {"room": "buero", "paired": True, "camera_enabled": True})
        self.assertEqual(hass.transport.rooms["buero"], "tablet")
        self.assertEqual(hass.transport.settings["buero"]["wake_device_id"], did)
        self.assertEqual(hass.devices[did]["user_id"], "tablet")
        self.assertEqual(hass.saved, 1)
        # Idempotent enable only. No owner transfer and no duplicate room.
        again = await self.action(hass, hass.admin, {
            "action": "camera_setup", "room": "buero", "device_id": did})
        self.assertTrue(again["paired"])
        self.assertEqual(len(hass.transport.rooms), 1)

    async def test_camera_setup_rejects_cross_room_and_wrong_ownership(self):
        hass = Fixture()
        did = "d" * 32
        hass.devices[did] = {"device_id": did, "room": "Büro", "user_id": "tablet"}
        await self.action(hass, hass.admin, {
            "action": "create", "room": "wohnzimmer", "user_id": "tablet"})
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "camera_setup", "room": "buero", "device_id": did})
        self.assertNotIn("buero", hass.transport.rooms)
        # A different HA user must not be able to bind someone else's tablet.
        hass.transport.rooms.clear()
        hass.transport.rooms["buero"] = "admin"
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "camera_setup", "room": "buero", "device_id": did})
        self.assertNotIn("buero", hass.transport.settings)

    async def test_non_admin_cannot_read_or_create_rooms(self):
        hass = Fixture()
        for action in ("list", "create"):
            with self.assertRaises(PermissionError):
                await self.action(hass, hass.user, {
                    "action": action, "room": "buero", "user_id": "tablet"})

    async def test_camera_requires_admin_owner_and_explicit_boolean(self):
        hass = Fixture()
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        view = await self.action(hass, hass.admin, {"action": "list"})
        self.assertFalse(view["rooms"][0]["camera_enabled"])
        response = await self.action(hass, hass.admin, {
            "action": "camera", "room": "buero", "user_id": "tablet",
            "camera_enabled": True})
        self.assertTrue(response["camera_enabled"])
        self.assertTrue(hass.transport.settings["buero"]["camera_enabled"])
        self.assertTrue((await self.action(hass, hass.admin, {"action": "list"}))["rooms"][0]["camera_enabled"])
        for invalid in ({"room": "buero", "user_id": "tablet", "camera_enabled": "true"},
                        {"room": "elsewhere", "user_id": "tablet", "camera_enabled": True},
                        {"room": "buero", "user_id": "admin", "camera_enabled": True}):
            with self.assertRaises(ValueError):
                await self.action(hass, hass.admin, {"action": "camera", **invalid})
        with self.assertRaises(PermissionError):
            await self.action(hass, hass.user, {
                "action": "camera", "room": "buero", "user_id": "tablet",
                "camera_enabled": False})
        await self.action(hass, hass.admin, {
            "action": "camera", "room": "buero", "user_id": "tablet",
            "camera_enabled": False})
        self.assertFalse(hass.transport.settings["buero"]["camera_enabled"])

    async def test_unpair_stops_room_session_and_can_repair(self):
        hass = Fixture()
        did = "a" * 32
        hass.devices[did] = {"device_id": did, "room": "Büro", "user_id": "tablet"}
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        await self.action(hass, hass.admin, {
            "action": "pair", "room": "buero", "user_id": "tablet",
            "device_id": did})
        hass.transport.settings["buero"]["camera_enabled"] = True
        hass.sessions["buero"] = "active"
        hass.jobs["old-job"] = "buero"
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "unpair", "room": "buero", "user_id": "tablet",
                "device_id": did, "confirmed": False})
        result = await self.action(hass, hass.admin, {
            "action": "unpair", "room": "buero", "user_id": "tablet",
            "device_id": did, "confirmed": True})
        self.assertTrue(result["unpaired"])
        self.assertEqual(hass.transport.rooms["buero"], "tablet")
        self.assertNotIn("wake_device_id", hass.transport.settings["buero"])
        self.assertFalse(hass.transport.settings["buero"]["camera_enabled"])
        self.assertFalse(hass.sessions)
        self.assertFalse(hass.jobs)
        self.assertIn(did, hass.devices)
        await self.action(hass, hass.admin, {
            "action": "pair", "room": "buero", "user_id": "tablet",
            "device_id": did})
        self.assertEqual(hass.transport.settings["buero"]["wake_device_id"], did)

    async def test_delete_room_releases_owner_without_deleting_ha_user(self):
        hass = Fixture()
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        hass.transport.settings["buero"] = {"camera_enabled": True}
        hass.sessions["buero"] = "active"
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "delete_room", "room": "buero",
                "user_id": "admin", "confirmed": True})
        result = await self.action(hass, hass.admin, {
            "action": "delete_room", "room": "buero",
            "user_id": "tablet", "confirmed": True})
        self.assertTrue(result["removed"])
        self.assertNotIn("buero", hass.transport.rooms)
        self.assertNotIn("buero", hass.transport.settings)
        self.assertNotIn("buero", hass.sessions)
        self.assertEqual(hass.cleaned_rooms, ["buero"])
        self.assertIsNotNone(await hass.auth.async_get_user("tablet"))
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        self.assertEqual(hass.transport.rooms["buero"], "tablet")

    async def test_delete_tablet_clears_pairings_but_keeps_rooms(self):
        hass = Fixture()
        did = "b" * 32
        hass.devices[did] = {"device_id": did, "room": "Büro", "user_id": "tablet"}
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        await self.action(hass, hass.admin, {
            "action": "pair", "room": "buero", "user_id": "tablet",
            "device_id": did})
        hass.transport.settings["buero"]["camera_enabled"] = True
        hass.sessions["buero"] = "active"
        with self.assertRaises(PermissionError):
            await self.action(hass, hass.user, {
                "action": "delete_device", "device_id": did,
                "confirmed": True})
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "delete_device", "device_id": did})
        result = await self.action(hass, hass.admin, {
            "action": "delete_device", "device_id": did, "confirmed": True})
        self.assertTrue(result["removed"])
        self.assertNotIn(did, hass.devices)
        self.assertFalse(hass.sessions)
        self.assertEqual(hass.transport.rooms["buero"], "tablet")
        self.assertNotIn("wake_device_id", hass.transport.settings["buero"])
        self.assertFalse(hass.transport.settings["buero"]["camera_enabled"])
        self.assertEqual(hass.cleaned_tablets, [did])
        self.assertIsNotNone(await hass.auth.async_get_user("tablet"))

    async def test_pairing_respects_user_ownership(self):
        hass = Fixture()
        identifier = "a" * 32
        hass.devices[identifier] = {"device_id": identifier,
                                    "room": "Büro", "user_id": "admin"}
        await self.action(hass, hass.admin, {
            "action": "create", "room": "buero", "user_id": "tablet"})
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "pair", "room": "buero", "user_id": "tablet",
                "device_id": identifier})
        response = await self.action(hass, hass.admin, {
            "action": "pair", "room": "buero", "user_id": "tablet",
            "device_id": identifier, "transfer_device": True})
        self.assertTrue(response["paired"])
        self.assertEqual(hass.devices[identifier]["user_id"], "tablet")
        self.assertEqual(hass.transport.settings["buero"]["wake_device_id"],
                         identifier)


if __name__ == "__main__":
    unittest.main()
