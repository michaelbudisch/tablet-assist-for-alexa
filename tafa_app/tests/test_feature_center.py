"""TAFA guided feature and mapping tests; no Home Assistant installation needed."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from feature_center import (FEATURES, SOURCE_DOMAINS, eligible, ordered_candidates,
                            save_source_group, save_announcement_room,
                            render_feature_center, render_announcement_rooms,
                            add_dashboard_module, _selected)


def fields(feature_id, **values):
    return {"csrf": ["test"], "lang": ["de"], "tab": ["features"],
            "action": ["feature_sources"], "feature_id": [feature_id],
            **{"source_" + k: [v] for k, v in values.items()}}


class FeatureCenterTests(unittest.TestCase):
    def test_every_source_is_in_one_catalog_feature(self):
        self.assertEqual({k for item in FEATURES for k in item[5]}, set(SOURCE_DOMAINS))
        self.assertEqual(len({item[0] for item in FEATURES}), len(FEATURES))

    def test_oil_source_changes_are_non_destructive(self):
        initial = {
            "sources_json": json.dumps({"heizoel": "sensor.oil_old",
                                        "vorlauf": "sensor.flow", "weather": "weather.home"}),
            "rooms_json": "{}",
        }
        inventory = [{"id": "sensor.oil_new", "name": "Oil", "unit": "L", "online": True}]
        result = save_source_group(fields("fuel", heizoel="sensor.oil_new", oelverbrauch=""), initial, inventory)
        new = json.loads(result["sources_json"])
        self.assertEqual(new["heizoel"], "sensor.oil_new")
        self.assertEqual(new["vorlauf"], "sensor.flow")
        self.assertEqual(new["weather"], "weather.home")

    def test_unsupported_unit_or_domain_is_rejected(self):
        initial = {"sources_json": "{}", "rooms_json": "{}"}
        inventory = [{"id": "sensor.random", "name": "random", "unit": "W", "online": True}]
        with self.assertRaises(ValueError):
            save_source_group(fields("fuel", heizoel="sensor.random", oelverbrauch=""), initial, inventory)
        with self.assertRaises(ValueError):
            save_source_group(fields("fuel", heizoel="switch.invalid", oelverbrauch=""), initial, inventory)
        with self.assertRaises(ValueError):
            save_source_group(fields("fuel", heizoel="sensor.not_registered", oelverbrauch=""), initial, inventory)

    def test_missing_previous_sensor_can_remain_without_deleting_it(self):
        previous = {"sources_json": '{"heizoel":"sensor.legacy","vorlauf":"sensor.flow"}',
                    "rooms_json": "{}"}
        result = save_source_group(fields("fuel", heizoel="sensor.legacy", oelverbrauch=""), previous, [])
        self.assertEqual(json.loads(result["sources_json"])["heizoel"], "sensor.legacy")
        self.assertEqual(json.loads(result["sources_json"])["vorlauf"], "sensor.flow")

    def test_candidates_use_units_and_allow_current_missing_entity(self):
        entities = [{"id": "sensor.oil", "name": "Öltank", "unit": "L", "online": True},
                    {"id": "sensor.watts", "name": "Leistung", "unit": "W", "online": True}]
        self.assertEqual([e["id"] for e in ordered_candidates("heizoel", entities)], ["sensor.oil"])
        html = render_feature_center({"sources_json": '{"heizoel":"sensor.last_seen"}'},
                                     "de", "test", entities, True, [])
        self.assertIn("sensor.last_seen", html)
        self.assertNotIn("sensor.watts", html.split('id="feature-fuel"')[1].split("</article>")[0])
        self.assertIn("Funktionen nach Bedarf", html)

    def test_add_module_only_appends_without_mutating_saved_config(self):
        saved = {"type": "custom:tafa-home-dashboard", "version": 1,
                 "modules": ["assist", "heating"], "bindings": {"fuel_volume": ["sensor.personal"]},
                 "presentation": {"captions": False}}
        calls = []
        def command(token, action, config=None):
            calls.append((action, config))
            return {"config": saved} if action == "get" else {"saved": True}
        with patch("feature_center._dashboard_command", side_effect=command):
            self.assertTrue(add_dashboard_module("token", "fuel"))
        updated = calls[-1][1]
        self.assertEqual(updated["modules"], ["assist", "heating", "fuel"])
        self.assertEqual(updated["bindings"], {"fuel_volume": ["sensor.personal"]})
        self.assertEqual(updated["presentation"], {"captions": False})
        self.assertEqual(saved["modules"], ["assist", "heating"])
        with patch("feature_center._dashboard_command", side_effect=command):
            self.assertFalse(add_dashboard_module("token", "heating"))

    def test_room_form_preserves_other_rooms(self):
        previous = {"rooms_json": json.dumps({"Büro": {"notify": "notify.echo_old"},
                                               "Wohnzimmer": {"notify": "notify.living"}}),
                    "mp3_base": "http://192.168.1.50:5001",
                    "public_audio_base": "https://tafa.example.org"}
        data = {"csrf": ["test"], "lang": ["de"], "tab": ["features"],
                "action": ["feature_room"], "room_name": ["Büro"],
                "notify": ["notify.echo_new"], "dnd": [""], "quiet": [""]}
        result = save_announcement_room(data, previous, [], ["notify.echo_new"])
        rooms = json.loads(result["rooms_json"])
        self.assertEqual(rooms["Büro"]["notify"], "notify.echo_new")
        self.assertEqual(rooms["Wohnzimmer"]["notify"], "notify.living")
        view = render_announcement_rooms(previous, "de", "test", [], [])
        self.assertIn("notify.echo_old", view)


if __name__ == "__main__":
    unittest.main()
