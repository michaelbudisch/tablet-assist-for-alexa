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
        self.assertNotIn('name="action" value="room_create"', html)
        self.assertIn("Home-Assistant-Räume", html)
        pair = html.split('<form class="tafa-area-form"', 1)[1].split('</form>', 1)[0]
        self.assertEqual(pair.count('name="device_id"'), 1)
        self.assertEqual(pair.count('name="area_id"'), 1)

    def test_room_camera_explicit_opt_in_without_any_tablet(self):
        with patch.object(panel, "ws_call", return_value={"camera_enabled": True}) as api:
            result = panel.set_room_camera({
                "room": ["buero"], "user_id": ["user1"],
                "camera_enabled": ["true"]})
            self.assertIn("aktiviert", result)
            self.assertEqual(api.call_args.args, ("camera",))
            self.assertEqual(api.call_args.kwargs,
                {"room": "buero", "user_id": "user1", "camera_enabled": True})
        state = {"devices": [{"device_id": ID, "room": "Tablet", "online": True}],
                 "rooms": [{"room": "buero", "user_id": "user1",
                            "wake_device_id": ID, "camera_enabled": False}],
                 "areas": [{"area_id": "buero", "name": "Büro"}],
                 "users": [{"id": "user1", "name": "Tablet Benutzer"}],
                 "error": "", "room_error": ""}
        html = panel.render_device_center("de", "csrf", state)
        self.assertIn('name="action" value="room_camera"', html)
        self.assertIn('name="camera_enabled"', html)
        self.assertIn('value="false" selected', html)
        state["rooms"][0]["camera_enabled"] = True
        self.assertIn('value="true" selected',panel.render_device_center("de","csrf",state))
        for val in ("yes", "", "1"):
            with self.assertRaises(ValueError):
                panel.set_room_camera({"room": ["buero"], "user_id": ["user1"],
                                       "camera_enabled": [val]})

    def test_assign_one_ha_area_without_room_user_form(self):
        with patch.object(panel, "ws_call", return_value={"paired": True}) as api:
            self.assertIn("Home-Assistant-Raum", panel.assign_to_ha_area({
                "device_id": [ID], "area_id": ["wohnzimmer"]}))
            self.assertEqual(api.call_args.args, ("assign_area",))
            self.assertEqual(api.call_args.kwargs,
                             {"device_id": ID, "area_id": "wohnzimmer"})
        for room in ("", "../bad", "BÜRO"):
            with self.assertRaises(ValueError):
                panel.assign_to_ha_area({"device_id": [ID], "area_id": [room]})
        page = panel.render_device_center("de", "csrf", {
            "devices": [{"device_id": ID, "room": "TAFA Tablet", "online": True}],
            "rooms": [{"room": "wohnzimmer", "user_id": "owner", "wake_device_id": ID}],
            "areas": [{"area_id": "wohnzimmer", "name": "Wohnzimmer"},
                      {"area_id": "buero", "name": "Büro"}],
            "users": [{"id": "owner", "name": "Room User"}]})
        self.assertEqual(page.count('name="action" value="area_assign"'), 1)
        self.assertNotIn('name="action" value="room_pair"', page)
        self.assertNotIn('name="action" value="room_create"', page)
        self.assertNotIn('name="transfer_device"', page)
        self.assertIn('name="area_id"', page)
        self.assertIn('value="wohnzimmer" selected', page)
        self.assertIn("<details", page)
        self.assertIn("Erweitert:", page)
        self.assertNotIn('name="setting" value="room"', page)


    def test_reset_actions_need_explicit_confirmation(self):
        with patch.object(panel, "ws_call", return_value={"removed": True}) as api:
            panel.remove_device({"device_id": [ID], "confirm": ["1"]})
            self.assertEqual(api.call_args.args, ("delete_device",))
            self.assertTrue(api.call_args.kwargs["confirmed"])
            panel.unpair_device({"device_id": [ID], "room": ["buero"],
                                 "user_id": ["tablet"], "confirm": ["1"]})
            self.assertEqual(api.call_args.args, ("unpair",))
            panel.delete_room({"room": ["buero"], "user_id": ["tablet"],
                               "confirm": ["1"]})
            self.assertEqual(api.call_args.args, ("delete_room",))
        for callback, fields in (
            (panel.remove_device, {"device_id": [ID]}),
            (panel.unpair_device, {"device_id": [ID], "room": ["buero"], "user_id": ["tablet"]}),
            (panel.delete_room, {"room": ["buero"], "user_id": ["tablet"]}),
            (panel.delete_room, {"room": ["../bad"], "user_id": ["tablet"], "confirm": ["1"]}),
            (panel.remove_device, {"device_id": ["x"], "confirm": ["1"]}),
        ):
            with self.assertRaises(ValueError):
                callback(fields)

    def test_reset_buttons_are_scoped_to_correct_room_and_tablet(self):
        page = panel.render_device_center("de", "nonce", {
            "devices": [{"device_id": ID, "room": "Tablet", "online": False}],
            "rooms": [{"room": "buero", "user_id": "tablet",
                       "wake_device_id": ID}],
            "users": [{"id": "tablet", "name": "Tablet Büro"}],
            "error": "", "room_error": ""})
        for action in ("device_delete", "room_unpair", "room_delete"):
            self.assertIn(f'name="action" value="{action}"', page)
        self.assertIn('name="confirm" type="checkbox" value="1" required', page)
        self.assertIn('name="user_id" value="tablet"', page)
        self.assertIn('name="device_id" value="' + ID + '"', page)
        self.assertIn("HA-Benutzer", page)
        self.assertIn("Automationen", page)

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
        self.assertIn("Home-Assistant-Räume verwalten", page)
        self.assertNotIn('name="action" value="room_create"', page)
        self.assertNotIn('name="action" value="room_pair"', page)

    def test_empty_server_explains_missing_user(self):
        page = panel.render_device_center("de", "nonce", {
            "devices": [], "rooms": [], "users": [],
            "error": "", "room_error": ""})
        self.assertIn("Home-Assistant-Räume verwalten", page)
        self.assertIn("Nicht-Admin-HA-Konto", page)
        self.assertNotIn('name="action" value="room_create"', page)
        self.assertNotIn('name="action" value="area_assign"', page)

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
        self.assertEqual(state["users"][0]["name"], "Tablet Nutzer")
        self.assertNotIn('name="user_id"', panel.render_device_center("de", "csrf", state))

    def test_websocket_denial_shows_code_without_secret(self):
        with patch.object(panel, "ws_call",
                          side_effect=RuntimeError("TAFA WebSocket: unauthorized")):
            state = panel.read_device_data()
        self.assertEqual(state["error"], "TAFA WebSocket: unauthorized")
        self.assertIn("TAFA WebSocket: unauthorized", panel.render_device_center("de", "csrf", state))
        self.assertNotIn('name="action" value="area_assign"',
                      panel.render_device_center("de", "csrf", state))


if __name__ == "__main__":
    unittest.main()
