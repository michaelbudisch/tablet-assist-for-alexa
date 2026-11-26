"""Regression tests for authenticated TAFA Devices room pairing.

Run as a standalone unittest without Home Assistant installed. The actual
admin API handler is loaded from source, not a copied implementation.
"""
import ast
import asyncio
import re
import types
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "custom_components/tablet_assist_for_alexa/relay/relay_room_adapter.py"
ID = "a" * 32


class Forbidden(Exception):
    pass


class BadRequest(Exception):
    pass


class ServiceUnavailable(Exception):
    pass


class FakeWeb:
    HTTPForbidden = Forbidden
    HTTPBadRequest = BadRequest
    HTTPServiceUnavailable = ServiceUnavailable

    @staticmethod
    def json_response(payload, status=200, headers=None):
        return {"status": status, **payload}


def load_view():
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RoomAudioAdminView")
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    names = {"HomeAssistantView": object, "web": FakeWeb, "re": re,
             "KEY_HASS": "hass", "DOMAIN": "jarvis_tablet_audio",
             "KEY": "room_audio"}
    exec(compile(module, str(PATH), "exec"), names)
    return names["RoomAudioAdminView"]


class User:
    def __init__(self, uid, admin=False, active=True):
        self.id = uid
        self.name = uid
        self.is_admin = admin
        self.is_active = active
        self.system_generated = False


class FakeTransport:
    def __init__(self):
        self.rooms = {"jarvis_tablet": "tablet1"}
        self.settings = {"jarvis_tablet": {"quiet_start": "", "quiet_end": ""}}
        self.sessions = {"jarvis_tablet": object()}
        self.provision_calls = []

    def status(self, principal, request_id=None):
        result = {"online": principal == "tablet1", "ready": True, "room": "jarvis_tablet"}
        if request_id is not None:
            result["stage"] = "done" if request_id == "b" * 32 else "unknown"
        return result

    def submit_room(self, room, path):
        self.test_submit = (room, path)
        return "b" * 32

    def cancel(self, principal, job_id):
        self.test_cancel = (principal, job_id)
        return True

    def provision(self, room, user):
        self.provision_calls.append((room, user))
        self.rooms[room] = user
        self.sessions.pop(room, None)


class FakeAuth:
    def __init__(self, users):
        self.users = {u.id: u for u in users}

    async def async_get_users(self):
        return list(self.users.values())

    async def async_get_user(self, uid):
        return self.users.get(uid)


class FakeHass:
    async def save_wake(self):
        self.wake_saves += 1

    def __init__(self):
        self.auth = FakeAuth([User("admin", admin=True), User("tablet1"),
                              User("tablet2")])
        self.transport = FakeTransport()
        self.controller = types.SimpleNamespace(
            devices={ID: {"user_id": "tablet1", "room": "Jarvis Tablet"}},
            lock=asyncio.Lock(), save=self.save_wake)
        self.saves = 0
        self.wake_saves = 0

        async def persist():
            self.saves += 1

        self.data = {"jarvis_tablet_audio": {
            "room_audio": self.transport,
            "wake_devices_dynamic": self.controller,
            "room_audio_save": persist,
        }}


class FakeRequest:
    def __init__(self, hass, body, admin=True):
        self.app = {"hass": hass}
        self.content_length = 200
        self.body = body
        self.user = User("admin", admin=True) if admin else User("tablet1")

    def get(self, key):
        return self.user if key == "hass_user" else None

    async def json(self):
        return self.body


class PairingTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.view = load_view()

    async def call(self, hass, payload, admin=True):
        return await self.view().post(FakeRequest(hass, payload, admin))

    async def test_fresh_room_can_be_created_without_tablet(self):
        hass = FakeHass()
        hass.transport.rooms.clear()
        hass.transport.settings.clear()
        hass.controller.devices.clear()
        result = await self.call(hass, {
            "action": "create", "room": "buero", "user_id": "tablet2"})
        self.assertTrue(result["created"])
        self.assertEqual(hass.transport.rooms, {"buero": "tablet2"})
        self.assertEqual(hass.saves, 1)
        self.assertEqual(hass.transport.provision_calls, [("buero", "tablet2")])
        self.assertNotIn("session", str(result))
        with self.assertRaises(Forbidden):
            await self.call(FakeHass(), {
                "action": "create", "room": "buero", "user_id": "tablet2"}, admin=False)

    async def test_create_room_rejects_overwrites_and_invalid_users(self):
        for change in (
            {"room": "jarvis_tablet", "user_id": "tablet2"},
            {"room": "buero", "user_id": "admin"},
            {"room": "buero", "user_id": "unknown"},
            {"room": "../bad", "user_id": "tablet2"},
            {"room": "buero", "user_id": "tablet1"},
        ):
            hass = FakeHass()
            result = await self.call(hass, {"action": "create", **change})
            self.assertEqual(result["status"], 400)
            self.assertEqual(hass.saves, 0)

    async def test_list_only_returns_admin_safe_information(self):
        hass = FakeHass()
        result = await self.call(hass, {"action": "list"})
        self.assertEqual(result["rooms"][0]["room"], "jarvis_tablet")
        self.assertTrue(result["rooms"][0]["online"])
        self.assertEqual(result["devices"][0]["owner_user_id"], "tablet1")
        self.assertEqual([u["id"] for u in result["users"]], ["tablet1", "tablet2"])
        self.assertNotIn("session", str(result))
        self.assertNotIn("token", str(result))

    async def test_existing_room_keeps_live_player_and_previous_settings(self):
        hass = FakeHass()
        session = hass.transport.sessions["jarvis_tablet"]
        result = await self.call(hass, {"action": "pair", "device_id": ID,
                         "user_id": "tablet1", "room": "jarvis_tablet"})
        self.assertTrue(result["paired"])
        self.assertEqual(hass.transport.provision_calls, [])
        self.assertIs(hass.transport.sessions["jarvis_tablet"], session)
        self.assertEqual(hass.transport.settings["jarvis_tablet"]["quiet_start"], "")
        self.assertEqual(hass.transport.settings["jarvis_tablet"]["wake_device_id"], ID)
        self.assertEqual(hass.saves, 1)

    async def test_unknown_user_wrong_owner_or_unregistered_device_is_rejected(self):
        for changes in (
            {"user_id": "admin"},
            {"user_id": "tablet2"},
            {"user_id": "unknown"},
            {"device_id": "b" * 32},
            {"room": "../foo"},
            {"replace": "true"},
        ):
            hass = FakeHass()
            params = {"action": "pair", "device_id": ID,
                      "user_id": "tablet1", "room": "jarvis_tablet"}
            params.update(changes)
            with self.subTest(changes=changes):
                response = await self.call(hass, params)
                self.assertEqual(response["status"], 400)
                self.assertEqual(hass.saves, 0)
                self.assertEqual(hass.transport.provision_calls, [])

    async def test_requires_real_admin_for_read_and_write(self):
        hass = FakeHass()
        for action in ("list", "pair"):
            with self.subTest(action=action), self.assertRaises(Forbidden):
                await self.call(hass, {"action": action}, admin=False)

    async def test_new_room_is_added_with_user_and_wake_device(self):
        hass = FakeHass()
        hass.transport.rooms = {}
        hass.transport.settings = {}
        hass.transport.sessions = {}
        result = await self.call(hass, {"action": "pair", "room": "jarvis_tablet",
                          "user_id": "tablet1", "device_id": ID})
        self.assertTrue(result["paired"])
        self.assertEqual(hass.transport.provision_calls,
                         [("jarvis_tablet", "tablet1")])
        self.assertEqual(hass.transport.settings["jarvis_tablet"]["wake_device_id"], ID)


    async def test_transfer_device_requires_explicit_admin_approval(self):
        hass = FakeHass()
        params = {"action": "pair", "device_id": ID, "room": "other",
                  "user_id": "tablet2"}
        first = await self.call(hass, params)
        self.assertEqual(first["status"], 400)
        self.assertEqual(hass.controller.devices[ID]["user_id"], "tablet1")
        # User tablet2 cannot simultaneously take over an existing room;
        # use an empty setup for this approved cross-account transfer.
        hass.transport.rooms = {}
        hass.transport.settings = {}
        accepted = await self.call(hass, {**params, "transfer_device": True})
        self.assertTrue(accepted["paired"])
        self.assertEqual(hass.controller.devices[ID]["user_id"], "tablet2")
        self.assertEqual(hass.wake_saves, 1)

    async def test_camera_is_opt_in_and_never_starts_by_default(self):
        hass = FakeHass()
        first = await self.call(hass, {"action": "list"})
        self.assertFalse(first["rooms"][0]["camera_enabled"])
        self.assertFalse(first["rooms"][0]["camera_online"])

        session = hass.transport.sessions["jarvis_tablet"]
        allowed = await self.call(hass, {"action": "camera", "room": "jarvis_tablet",
                                         "device_id": ID, "enabled": True})
        self.assertTrue(allowed["camera_enabled"])
        self.assertIs(hass.transport.sessions["jarvis_tablet"], session)
        self.assertTrue(hass.transport.settings["jarvis_tablet"]["camera_enabled"])
        self.assertEqual(hass.saves, 1)

        disabled = await self.call(hass, {"action": "camera", "room": "jarvis_tablet",
                                         "device_id": ID, "enabled": False})
        self.assertFalse(disabled["camera_enabled"])
        self.assertFalse(hass.transport.settings["jarvis_tablet"]["camera_enabled"])

    async def test_camera_permissions_require_admin_valid_room_and_boolean(self):
        for changes in (
            {"enabled": "true"}, {"enabled": 1}, {"device_id": "b" * 32},
            {"room": "unknown"},
        ):
            hass = FakeHass()
            payload = {"action": "camera", "room": "jarvis_tablet",
                       "device_id": ID, "enabled": True}
            payload.update(changes)
            with self.subTest(changes=changes):
                response = await self.call(hass, payload)
                self.assertEqual(response["status"], 400)
                self.assertEqual(hass.saves, 0)
        with self.assertRaises(Forbidden):
            await self.call(FakeHass(), {"action": "camera", "room": "jarvis_tablet",
                                        "device_id": ID, "enabled": True}, admin=False)



    async def test_admin_speech_test_targets_only_paired_room_and_local_audio(self):
        hass = FakeHass()
        base = {"action": "test", "room": "jarvis_tablet", "device_id": ID}
        status = await self.call(hass, {**base, "operation": "status"})
        self.assertEqual(status["room"], "jarvis_tablet")
        self.assertTrue(status["ready"])
        self.assertEqual(status["stage"], "unknown") if "stage" in status else None
        path = "/api/tts_proxy/" + "z" * 30
        result = await self.call(hass, {**base, "operation": "submit", "path": path})
        self.assertTrue(result["accepted"])
        self.assertEqual(result["id"], "b" * 32)
        self.assertEqual(hass.transport.test_submit, ("jarvis_tablet", path))
        stage = await self.call(hass, {**base, "operation": "status", "id": "b" * 32})
        self.assertEqual(stage["stage"], "done")
        stop = await self.call(hass, {**base, "operation": "cancel", "id": "b" * 32})
        self.assertTrue(stop["accepted"])
        self.assertEqual(hass.transport.test_cancel, ("tablet1", "b" * 32))

    async def test_speech_test_does_not_allow_cross_room_or_remote_audio(self):
        for values in (
            {"device_id": "c" * 32, "operation": "status"},
            {"room": "another", "operation": "status"},
            {"operation": "submit", "path": "https://example.org/secret"},
            {"operation": "submit", "path": "/api/tts_proxy/../../bad"},
            {"operation": "cancel", "id": "not-valid"},
            {"operation": "run"},
        ):
            hass = FakeHass()
            request = {"action": "test", "room": "jarvis_tablet", "device_id": ID}
            request.update(values)
            with self.subTest(values=values):
                result = await self.call(hass, request)
                self.assertEqual(result["status"], 400)
                self.assertEqual(hass.saves, 0)
        with self.assertRaises(Forbidden):
            await self.call(FakeHass(),
                {"action": "test", "operation": "status", "room": "jarvis_tablet", "device_id": ID},
                admin=False)

    async def test_reassignment_needs_explicit_replace(self):
        hass = FakeHass()
        hass.transport.rooms["jarvis_tablet"] = "tablet2"
        denied = await self.call(hass, {"action": "pair", "room": "jarvis_tablet",
                          "user_id": "tablet1", "device_id": ID})
        self.assertEqual(denied["status"], 400)
        self.assertEqual(hass.transport.provision_calls, [])
        allowed = await self.call(hass, {"action": "pair", "room": "jarvis_tablet",
                          "user_id": "tablet1", "device_id": ID, "replace": True})
        self.assertTrue(allowed["paired"])
        self.assertEqual(hass.transport.provision_calls,
                         [("jarvis_tablet", "tablet1")])


if __name__ == "__main__":
    unittest.main()
