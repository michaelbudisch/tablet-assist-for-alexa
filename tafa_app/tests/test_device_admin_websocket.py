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
        "ar": types.SimpleNamespace(async_get=lambda hass: hass.area_registry),
        "dr": types.SimpleNamespace(async_get=lambda hass: hass.device_registry),
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
        self.area_entries = {
            name: types.SimpleNamespace(id=name, name=display)
            for name, display in (("buero", "Büro"), ("wohnzimmer", "Wohnzimmer"))
        }
        self.area_registry = types.SimpleNamespace(
            async_list_areas=lambda: list(self.area_entries.values()),
            async_get_area=lambda name: self.area_entries.get(name),
        )
        self.area_assignments = {}
        def get_registered_device(identifiers):
            identifier = next(iter(identifiers))[1]
            if identifier not in self.devices:
                return None
            return types.SimpleNamespace(id=identifier,
                                         area_id=self.area_assignments.get(identifier))
        def update_registered_device(identifier, area_id):
            self.area_assignments[identifier] = area_id
        self.device_registry = types.SimpleNamespace(
            async_get_device_by_identifier=lambda domain, identifier: get_registered_device({(domain, identifier)}),
            async_update_device=update_registered_device,
        )
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

    async def test_assign_existing_ha_area_creates_one_secure_pairing(self):
        hass = Fixture()
        identifier = "a" * 32
        hass.devices[identifier] = {
            "device_id": identifier, "user_id": "tablet",
            "room": "TAFA Tablet", "online": True,
        }
        result = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": identifier, "area_id": "wohnzimmer"})
        self.assertTrue(result["paired"])
        self.assertEqual(result["room"], "wohnzimmer")
        self.assertEqual(hass.transport.rooms, {"wohnzimmer": "tablet"})
        self.assertEqual(hass.transport.settings["wohnzimmer"]["wake_device_id"], identifier)
        self.assertFalse(hass.transport.settings["wohnzimmer"]["camera_enabled"])
        self.assertEqual(hass.area_assignments[identifier], "wohnzimmer")
        self.assertEqual(hass.saved, 1)
        self.assertEqual(len((await self.action(hass, hass.admin, {"action": "list"}))["areas"]), 2)
        # Same ID / HA area is a safe idempotent assignment.
        again = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": identifier, "area_id": "wohnzimmer"})
        self.assertFalse(again["moved"])
        self.assertEqual(len(hass.transport.rooms), 1)

    async def test_assign_rejects_unregistered_area_and_wrong_owner(self):
        hass = Fixture()
        identifier = "a" * 32
        hass.devices[identifier] = {"device_id": identifier, "user_id": "tablet"}
        for area in ("no_such_area", "../bad"):
            with self.assertRaises(ValueError):
                await self.action(hass, hass.admin, {
                    "action": "assign_area", "device_id": identifier, "area_id": area})
        with self.assertRaises(PermissionError):
            await self.action(hass, hass.user, {
                "action": "assign_area", "device_id": identifier, "area_id": "buero"})
        # A second active user occupying the desired HA area is allowed;
        # each tablet receives an independent internal audio/camera route.
        hass.transport.rooms["buero"] = "tablet2"
        hass.transport.settings["buero"] = {"wake_device_id": "b"*32, "area_id": "buero"}
        accepted = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": identifier, "area_id": "buero"})
        self.assertTrue(accepted["paired"])
        self.assertEqual(accepted["audio_route"], "tafa_" + identifier)

    async def test_two_active_tablets_can_share_one_ha_area(self):
        hass = Fixture()
        first, second = "a"*32, "b"*32
        hass.auth.users["tablet2"] = User("tablet2", "Tablet Benutzer 2")
        hass.devices[first] = {"device_id": first, "user_id": "tablet",
                                "room": "Büro Tablet", "online": True}
        hass.devices[second] = {"device_id": second, "user_id": "tablet2",
                                 "room": "Sofa Tablet", "online": True}
        one = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": first, "area_id": "wohnzimmer"})
        two = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": second, "area_id": "wohnzimmer"})
        self.assertEqual(one["audio_route"], "wohnzimmer")
        self.assertEqual(two["audio_route"], "tafa_" + second)
        self.assertEqual(len(hass.transport.rooms), 2)
        self.assertEqual(len(set(hass.transport.rooms.values())), 2)
        self.assertEqual(hass.transport.settings["wohnzimmer"]["area_id"], "wohnzimmer")
        self.assertEqual(hass.transport.settings["tafa_" + second]["area_id"], "wohnzimmer")
        self.assertEqual(hass.area_assignments[first], "wohnzimmer")
        self.assertEqual(hass.area_assignments[second], "wohnzimmer")
        self.assertFalse(hass.transport.settings["tafa_" + second]["camera_enabled"])
        rooms = (await self.action(hass, hass.admin, {"action": "list"}))["rooms"]
        self.assertEqual({r["area_id"] for r in rooms}, {"wohnzimmer"})
        self.assertEqual({r["device_name"] for r in rooms}, {"Büro Tablet", "Sofa Tablet"})
        self.assertEqual({r["wake_device_id"] for r in rooms}, {first, second})
        again = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": second, "area_id": "wohnzimmer"})
        self.assertFalse(again["moved"])
        self.assertEqual(len(hass.transport.rooms), 2)

    async def test_two_tablets_cannot_share_the_same_ha_user(self):
        hass = Fixture()
        first, second = "a"*32, "b"*32
        hass.devices[first] = {"device_id": first, "user_id": "tablet", "online": True}
        hass.devices[second] = {"device_id": second, "user_id": "tablet", "online": True}
        await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": first, "area_id": "wohnzimmer"})
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "assign_area", "device_id": second, "area_id": "wohnzimmer"})
        self.assertEqual(len(hass.transport.rooms), 1)

    async def test_reinstall_replaces_only_offline_previous_device(self):
        hass = Fixture()
        old_id, new_id = "a"*32, "b"*32
        hass.devices[old_id] = {"device_id": old_id, "user_id": "tablet", "online": False}
        hass.devices[new_id] = {"device_id": new_id, "user_id": "tablet", "online": True}
        hass.transport.rooms["wohnzimmer"] = "tablet"
        hass.transport.settings["wohnzimmer"] = {"wake_device_id": old_id, "camera_enabled": True}
        result = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": new_id, "area_id": "wohnzimmer"})
        self.assertTrue(result["replaced_offline"])
        self.assertEqual(hass.transport.settings["wohnzimmer"]["wake_device_id"], new_id)
        self.assertTrue(hass.transport.settings["wohnzimmer"]["camera_enabled"])
        hass.transport.settings["wohnzimmer"]["wake_device_id"] = old_id
        hass.devices[old_id]["online"] = True
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "assign_area", "device_id": new_id, "area_id": "wohnzimmer"})
        self.assertEqual(hass.transport.settings["wohnzimmer"]["wake_device_id"], old_id)

    async def test_moving_same_tablet_updates_area_and_clears_old_camera_consent(self):
        hass = Fixture()
        identifier = "a"*32
        hass.devices[identifier] = {"device_id": identifier, "user_id": "tablet", "online": True}
        hass.transport.rooms["wohnzimmer"] = "tablet"
        hass.transport.settings["wohnzimmer"] = {
            "wake_device_id": identifier, "camera_enabled": True}
        with self.assertRaises(ValueError):
            await self.action(hass, hass.admin, {
                "action": "assign_area", "device_id": identifier, "area_id": "buero"})
        result = await self.action(hass, hass.admin, {
            "action": "assign_area", "device_id": identifier,
            "area_id": "buero", "confirm_move": True})
        self.assertTrue(result["moved"])
        self.assertEqual(hass.transport.rooms, {"buero": "tablet"})
        self.assertEqual(hass.cleaned_rooms, ["wohnzimmer"])
        self.assertFalse(hass.transport.settings["buero"]["camera_enabled"])
        self.assertEqual(hass.area_assignments[identifier], "buero")

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
