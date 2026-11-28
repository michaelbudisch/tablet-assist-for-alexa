"""Pure regression tests: HA-area announcements vs per-tablet private audio."""
import ast
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "custom_components" / "tablet_assist_for_alexa" / "relay" / "relay_room_audio.py"

def load_expander():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(node for node in tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "expand_area_targets")
    env = {"ROOM": re.compile(r"[a-z0-9][a-z0-9_-]{0,63}"), "MAX_ROOMS": 24}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])),
                 str(SOURCE), "exec"), env)
    return env["expand_area_targets"]

class AreaAudioTest(unittest.TestCase):
    def test_two_tablets_in_same_ha_area_broadcast_to_both(self):
        first, second = "wohnzimmer", "tafa_"+"b"*32
        rooms = {first: "user1", second: "user2"}
        settings = {first: {"area_id": "wohnzimmer", "wake_device_id": "a"*32},
                    second: {"area_id": "wohnzimmer", "wake_device_id": "b"*32}}
        resolve = load_expander()
        self.assertEqual(resolve(rooms, settings, ["wohnzimmer"]), [first, second])
        self.assertEqual(resolve(rooms, settings, [second]), [second])
        self.assertEqual(resolve(rooms, settings, ["wohnzimmer", second]), [first, second])
        with self.assertRaises(ValueError):
            resolve(rooms, settings, ["buero"])

    def test_legacy_room_name_keeps_original_announcement(self):
        resolve = load_expander()
        self.assertEqual(resolve({"wohnzimmer": "user1"}, {}, ["wohnzimmer"]), ["wohnzimmer"])
        with self.assertRaises(ValueError):
            resolve({}, {}, ["wohnzimmer"])

if __name__ == "__main__":
    unittest.main()
