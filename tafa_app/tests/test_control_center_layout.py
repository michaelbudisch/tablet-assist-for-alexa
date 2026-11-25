"""Control Center redesign: navigation, accessibility and security contracts."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import server


class ControlCenterLayoutTests(unittest.TestCase):
    def mock_view(self, **kw):
        opts={"choose_speech_source":("external","http://192.168.1.5:5000"),
              "external_piper_ready":True, "local_model_inventory":{"piper_bytes":0,"whisper_bytes":0},
              "status":{"tablet_assist_for_alexa":"installed"},
              "setup_status":{"status":"configured"}, "discover_wyoming_stt":[],
              "setup_settings":{"gpu_base":"http://192.168.1.6:10502","mp3_base":""},
              "connection_status":{"gpu":"ready","gpu_version":"","piper":"ready","mp3":"not_configured","route":"qwen"},
              "assess_endpoints":{"gpu_base":"ready","cpu_stt":"missing"}}
        opts.update(kw)
        return opts

    def test_four_accessible_tabs_in_both_languages(self):
        configs=self.mock_view()
        with patch.object(server,"choose_speech_source",return_value=configs["choose_speech_source"]),\
             patch.object(server,"external_piper_ready",return_value=True),\
             patch.object(server,"local_model_inventory",return_value=configs["local_model_inventory"]),\
             patch.object(server,"status",return_value=configs["status"]),\
             patch.object(server,"setup_status",return_value=configs["setup_status"]),\
             patch.object(server,"discover_wyoming_stt",return_value=[]),\
             patch.object(server,"setup_settings",return_value=configs["setup_settings"]),\
             patch.object(server,"connection_status",return_value=configs["connection_status"]),\
             patch.object(server,"assess_endpoints",return_value=configs["assess_endpoints"]),\
             patch.object(server,"recent_stt_backend",return_value=None):
            de=server.display(lang="de",default_tab="connections")
            en=server.display(lang="en",default_tab="setup")
        self.assertEqual(de.count('role="tab"'),4)
        self.assertEqual(de.count('role="tabpanel"'),4)
        self.assertIn('data-default-tab="connections"',de)
        self.assertIn('data-default-tab="setup"',en)
        self.assertIn("Wartung &amp; Hilfe",de)
        self.assertIn("Connections",en)
        self.assertIn('href="#connections"',de)
        self.assertIn('id="tafa-settings"',de)
        self.assertIn("GPU-Whisper",de)
        self.assertNotIn("<style>",de)
        self.assertNotIn("<script>",de)
        self.assertIn('src="assets/control-center.js?v=',de)

    def test_assets_include_responsive_themes_and_accessible_tab_keyboard(self):
        css=(APP/"control_center.css").read_text()
        js=(APP/"control_center.js").read_text()
        self.assertIn("prefers-color-scheme:dark",css)
        self.assertIn("max-width:650px",css)
        self.assertIn("prefers-reduced-motion",css)
        self.assertIn('event.key',js)
        self.assertIn("ArrowRight",js)
        self.assertIn("hashchange",js)
        self.assertIn("panels[i].hidden",js)
        self.assertNotIn("innerHTML",js)
        self.assertIn("form",server.display(lang="en"))

    def test_invalid_default_tab_uses_overview(self):
        self.assertIn('data-default-tab="overview"',
                      server.display(default_tab="unknown-tab"))


if __name__=="__main__":
    unittest.main()
