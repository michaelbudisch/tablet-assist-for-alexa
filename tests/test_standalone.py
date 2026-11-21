"""Check the shipped UI and automatic registration without a live HA instance."""
import json
import unittest
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "custom_components/tablet_assist_for_alexa"

class Standalone(unittest.TestCase):
    def test_panel_files_and_lifecycle(self):
        src = (D / "__init__.py").read_text()
        self.assertIn("await panel_custom.async_register_panel(", src)
        self.assertIn("frontend.async_remove_panel(hass, DOMAIN)", src)
        self.assertIn("/tablet_assist_for_alexa/panel.js", src)
        panel = (D / "frontend/panel.js").read_text()
        for part in ("tablet-assist-panel", "assist/show", "tablet-assist-bt-keepalive", 'callService("tablet_assist_for_alexa","announce"'):
            self.assertIn(part, panel)
        for forbidden in ("hauszentrale", "input_select.jarvis", "input_text.jarvis", "__JARVIS_"):
            self.assertNotIn(forbidden, panel.lower())
        manifest = json.loads((D / "manifest.json").read_text())
        self.assertIn("panel_custom", manifest["dependencies"])
        self.assertIn("frontend", manifest["dependencies"])

    def test_translation_parity(self):
        def shape(obj):
            return {k:shape(v) for k,v in obj.items()} if isinstance(obj,dict) else None
        en = json.loads((D / "translations/en.json").read_text())
        de = json.loads((D / "translations/de.json").read_text())
        self.assertEqual(shape(en), shape(de))
        self.assertEqual(en, json.loads((D / "strings.json").read_text()))
        self.assertEqual(set(en["selector"]), {"hardware_profile","live_profile","voice_variant","conversation_mode","mp3_profile","rooms"})

if __name__ == "__main__":
    unittest.main()
