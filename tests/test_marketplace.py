"""Source-level marketplace and announcement checks (no HA instance)."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "tablet_assist_for_alexa"
DIR = ROOT / "custom_components" / DOMAIN
spec = importlib.util.spec_from_file_location("announcement", DIR / "announcement.py")
ann = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ann)

class Marketplace(unittest.TestCase):
    def test_layout(self):
        meta = json.loads((ROOT / "hacs.json").read_text())
        self.assertEqual(meta["homeassistant"], "2026.11.0")
        self.assertEqual([p.name for p in (ROOT/"custom_components").iterdir() if p.is_dir()], [DOMAIN])
        m = json.loads((DIR/"manifest.json").read_text())
        self.assertEqual(m["domain"], DOMAIN)
        self.assertEqual(m["version"], (ROOT/"VERSION").read_text().strip())
        self.assertTrue(m["config_flow"])
        for name in ["__init__.py", "config_flow.py", "stt.py", "tts.py", "conversation.py",
                     "translations/de.json", "translations/en.json", "frontend/assist.js", "frontend/keepalive.js",
                     "frontend/visual_client.js", "visual_ws.py"]:
            self.assertTrue((DIR/name).is_file(), name)
        for f in DIR.rglob("*.py"):
            self.assertNotIn("__JARVIS_", f.read_text(), str(f))

    def test_url(self):
        path = "/" + "a"*32 + ".mp3"
        self.assertEqual(ann.audio_url("https://audio.example.org", {"success":True,"path":path}),"https://audio.example.org"+path)
        for bad in ["//other.example.org/a.mp3", "/generate", "/"+ "a"*32 + ".mp3?x=1", "/"+ "A"*32 + ".mp3"]:
            with self.assertRaises(ValueError):
                ann.audio_url("https://audio.example.org", {"success":True,"path":bad})
        with self.assertRaises(ValueError):
            ann.audio_url("http://audio.example.org", {"success":True,"path":path})

    def test_routing(self):
        cfg = {"Büro":{"notify":"notify.office","quiet":"schedule.office","dnd":"switch.office"}}
        states = {k:SimpleNamespace(state="off") for k in ["notify.office","schedule.office","switch.office"]}
        self.assertEqual(ann.allowed_targets(cfg, ["Büro","Wohnzimmer","Büro"], states.get), ["notify.office"])
        states["schedule.office"].state = "on"
        self.assertEqual(ann.allowed_targets(cfg, ["Büro"], states.get), [])
        del states["schedule.office"]
        self.assertEqual(ann.allowed_targets(cfg, ["Büro"], states.get), [])

if __name__ == "__main__":
    unittest.main()
