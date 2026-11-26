"""Check the shipped UI and automatic registration without a live HA instance."""
import json
import re
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "custom_components/tablet_assist_for_alexa"

class Standalone(unittest.TestCase):
    def test_panel_files_and_lifecycle(self):
        src = (D / "__init__.py").read_text()
        self.assertNotIn("panel_custom.async_register_panel(", src)
        self.assertNotIn("frontend.async_remove_panel(hass, DOMAIN)", src)
        self.assertIn("/tablet_assist_for_alexa/panel.js", src)
        panel = (D / "frontend/panel.js").read_text()
        voice = (D / "frontend/voice_tools.js").read_text()
        dashboard = (D / "frontend/dashboard.js").read_text()
        for part in ("tablet-assist-panel", "tafa-home-dashboard",
                     "dashboard/get", "dashboard/set", "tablet-assist-voice-tools"):
            self.assertIn(part, panel)
        for part in ("assist/show", "tablet-assist-bt-keepalive",
                     'callService("tablet_assist_for_alexa","announce"'):
            self.assertIn(part, voice)
        self.assertIn("tafa-open-voice-tools", dashboard)
        for forbidden in ("input_select.jarvis", "input_text.jarvis", "__JARVIS_"):
            self.assertNotIn(forbidden, panel.lower())
        manifest = json.loads((D / "manifest.json").read_text())
        self.assertIn("panel_custom", manifest["dependencies"])
        self.assertIn("frontend", manifest["dependencies"])
        flow=(D / 'config_flow.py').read_text()
        self.assertIn('dashboard_only',flow)

    def test_translation_parity(self):
        def shape(obj):
            return {k:shape(v) for k,v in obj.items()} if isinstance(obj,dict) else None
        en = json.loads((D / "translations/en.json").read_text())
        de = json.loads((D / "translations/de.json").read_text())
        self.assertEqual(shape(en), shape(de))
        self.assertEqual(en, json.loads((D / "strings.json").read_text()))
        self.assertEqual(set(en["selector"]), {"hardware_profile","live_profile","voice_variant","conversation_mode","mp3_profile","rooms"})
        for k,v in en["selector"].items():
            for key in v["options"]:
                self.assertRegex(key, r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$")
        self.assertIn("@websocket_api.require_admin", (D / "learning_ws.py").read_text())

if __name__ == "__main__":
    unittest.main()
