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
        with patch.object(panel, "ha_call", return_value={"device": {}}) as api:
            self.assertEqual(panel.update_device({
                "device_id": [ID], "setting": ["mic_gain"],
                "value": ["120"]}), "Tablet setting saved.")
            self.assertEqual(api.call_args.args[1]["settings"], {"mic_gain": 120})
            panel.update_device({"device_id": [ID], "setting": ["muted"],
                                 "value": ["true"]})
            self.assertEqual(api.call_args.args[1]["settings"], {"muted": True})
        for bad in ({"device_id": [ID], "setting": ["mic_gain"], "value": ["999"]},
                    {"device_id": ["not-valid"], "setting": ["muted"], "value": ["true"]},
                    {"device_id": [ID], "setting": ["shell_command"], "value": ["1"]}):
            with self.assertRaises(ValueError):
                panel.update_device(bad)

    def test_pairing_cannot_replace_or_transfer(self):
        with patch.object(panel, "ha_call", return_value={}) as api:
            panel.pair_device({"device_id": [ID], "room": ["buero"],
                               "user_id": ["authorized-user"]})
            self.assertFalse(api.call_args.args[1]["replace"])
            self.assertFalse(api.call_args.args[1]["transfer_device"])

    def test_escapes_device_values_and_only_one_device_id_on_pair_form(self):
        html = panel.render_device_center("de", "csrf", {
            "devices": [{
                "device_id": ID, "room": "<img src=x onerror=evil>",
                "online": True, "word": "Jarvis",
                "telemetry": {"audio": "<script>alert(1)</script>"}}],
            "rooms": [], "users": [{"id": "user1", "name": "Raum 1"}],
            "error": ""})
        self.assertNotIn("<img", html)
        self.assertNotIn("<script", html)
        pair = html.split('class="pair-form"', 1)[1].split('</form>', 1)[0]
        self.assertEqual(pair.count('name="device_id"'), 1)

    def test_unavailable_backend_is_safe(self):
        with patch.object(panel, "ha_call", side_effect=OSError("secrets")):
            state = panel.read_device_data()
        self.assertEqual(state["error"], "OSError")
        self.assertEqual(state["room_error"], "OSError")
        self.assertNotIn("secrets", repr(state))
        self.assertIn("Tablet-Verbindung zu HA fehlgeschlagen",
                      panel.render_device_center("de", "x", state))

    def test_room_api_failure_does_not_hide_registered_tablets(self):
        def query(path, data):
            if path.endswith("/wake_devices"):
                return {"devices": [{"device_id": ID, "room": "Büro", "word": "Jarvis"}]}
            raise panel.urllib.error.HTTPError(
                url="https://secret.internal", code=403, msg="Bearer secret",
                hdrs=None, fp=None)
        with patch.object(panel, "ha_call", side_effect=query):
            state = panel.read_device_data()
        self.assertEqual(len(state["devices"]), 1)
        self.assertEqual(state["error"], "")
        self.assertEqual(state["room_error"], "HTTP 403")
        page = panel.render_device_center("de", "x", state)
        self.assertIn("Büro", page)
        self.assertIn("Multiroom-Verwaltung nicht erreichbar", page)
        self.assertIn("HTTP 403", page)
        self.assertNotIn("Bearer secret", page)
        self.assertNotIn("https://secret.internal", page)
        self.assertNotIn('class="pair-form"', page)


if __name__ == "__main__":
    unittest.main()
