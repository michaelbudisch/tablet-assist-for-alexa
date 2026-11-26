"""Regression tests for TAFA admin-only device control UI."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs
import re

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import device_center as panel

ID = "a" * 32


class DeviceCenterTests(unittest.TestCase):
    def test_control_backend_validation_and_boolean_switch(self):
        with patch.object(panel, "ws_call", return_value={"device": {}}) as api:
            self.assertEqual(panel.update_device({
                "device_id": [ID], "setting": ["mic_gain"],
                "value": ["120"]}), "Tablet setting saved.")
            self.assertEqual(api.call_args.kwargs["settings"], {"mic_gain": 120})
            panel.update_device({"device_id": [ID], "setting": ["muted"],
                                 "value": ["true"]})
            self.assertEqual(api.call_args.kwargs["settings"], {"muted": True})
        for bad in ({"device_id": [ID], "setting": ["mic_gain"], "value": ["999"]},
                    {"device_id": ["not-valid"], "setting": ["muted"], "value": ["true"]},
                    {"device_id": [ID], "setting": ["shell_command"], "value": ["1"]}):
            with self.assertRaises(ValueError):
                panel.update_device(bad)

    def test_pairing_cannot_replace_or_transfer(self):
        with patch.object(panel, "ws_call", return_value={}) as api:
            panel.pair_device({"device_id": [ID], "room": ["buero"],
                               "user_id": ["authorized-user"]})
            self.assertEqual(api.call_args.args, ("pair",))
            self.assertFalse(api.call_args.kwargs["transfer_device"])

    def test_escapes_device_values_and_only_one_device_id_on_pair_form(self):
        html = panel.render_device_center("de", "csrf", {
            "devices": [{
                "device_id": ID, "room": "<img src=x onerror=evil>",
                "online": True, "word": "Jarvis",
                "telemetry": {"audio": "<script>alert(1)</script>"}}],
            "rooms": [{"room": "buero", "user_id": "user1"}],
            "users": [{"id": "user1", "name": "Raum 1"}],
            "error": ""})
        self.assertNotIn("<img", html)
        self.assertNotIn("<script", html)
        self.assertIn('name="action" value="room_create"', html)
        pair = html.split('name="action" value="room_pair"', 1)[1].split('</form>', 1)[0]
        self.assertEqual(pair.count('name="device_id"'), 1)

    def test_create_room_without_any_tablet(self):
        with patch.object(panel, "ws_call", return_value={"created": True}) as api:
            self.assertIn("Raum angelegt", panel.create_room({
                "room": ["buero"], "user_id": ["user1"]}))
            self.assertEqual(api.call_args.args, ("create",))
            self.assertEqual(api.call_args.kwargs,
                             {"room": "buero", "user_id": "user1"})
        page = panel.render_device_center("de", "nonce", {
            "devices": [], "rooms": [],
            "users": [{"id": "user1", "name": "Room user"}],
            "error": "", "room_error": ""})
        self.assertIn("Neuen Raum anlegen", page)
        self.assertIn('name="action" value="room_create"', page)
        self.assertNotIn('name="action" value="room_pair"', page)

    def test_empty_server_explains_missing_user(self):
        page = panel.render_device_center("de", "nonce", {
            "devices": [], "rooms": [], "users": [],
            "error": "", "room_error": ""})
        self.assertIn("Neuen Raum anlegen", page)
        self.assertIn("Nicht-Admin-Benutzer", page)
        self.assertIn("Noch kein Nicht-Admin-Benutzer", page)
        self.assertIn('name="action" value="room_create"', page)
        self.assertIn('type="submit" disabled', page)

    def test_reject_invalid_room_name(self):
        for room in ("BÜRO", "../bad", "", "q"*65):
            with self.assertRaises(ValueError):
                panel.create_room({"room": [room], "user_id": ["user1"]})

    def test_owner_transfer_requires_explicit_checkbox(self):
        with patch.object(panel, "ws_call", return_value={}) as api:
            panel.pair_device({"device_id": [ID], "room": ["buero"],
                "user_id": ["user1"], "transfer_device": ["1"]})
            self.assertTrue(api.call_args.kwargs["transfer_device"])
        with self.assertRaises(ValueError):
            panel.pair_device({"device_id": [ID], "room": ["buero"],
                "user_id": ["user1"], "transfer_device": ["true"]})

    def test_unavailable_backend_is_safe(self):
        with patch.object(panel, "ws_call", side_effect=OSError("secrets")):
            state = panel.read_device_data()
        self.assertEqual(state["error"], "OSError")
        self.assertEqual(state["room_error"], "OSError")
        self.assertNotIn("secrets", repr(state))
        self.assertIn("Tablet-Verbindung zu HA fehlgeschlagen",
                      panel.render_device_center("de", "x", state))

    def test_websocket_lists_new_non_admin_user(self):
        with patch.object(panel, "ws_call", return_value={
            "devices": [], "rooms": [],
            "users": [{"id": "user123", "name": "Tablet Nutzer"}],
        }) as api:
            state = panel.read_device_data()
        self.assertEqual(api.call_args.args, ("list",))
        self.assertEqual(state["error"], "")
        self.assertIn("Tablet Nutzer", panel.render_device_center("de", "csrf", state))
        self.assertIn('value="user123"', panel.render_device_center("de", "csrf", state))

    def test_websocket_denial_shows_code_without_secret(self):
        with patch.object(panel, "ws_call",
                          side_effect=RuntimeError("TAFA WebSocket: unauthorized")):
            state = panel.read_device_data()
        self.assertEqual(state["error"], "TAFA WebSocket: unauthorized")
        self.assertIn("TAFA WebSocket: unauthorized", panel.render_device_center("de", "csrf", state))
        self.assertIn('type="submit" disabled',
                      panel.render_device_center("de", "csrf", state))


if __name__ == "__main__":
    unittest.main()
