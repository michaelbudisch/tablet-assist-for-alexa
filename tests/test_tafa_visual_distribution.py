"""Distribution contract: bundled TAFA contains the visual API and static module."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"custom_components"/"tablet_assist_for_alexa"
BUNDLE=ROOT/"tafa_app"/"bundle"/"tablet_assist_for_alexa"
class VisualDistribution(unittest.TestCase):
    def test_paths_and_registration(self):
        for base in (MAIN,BUNDLE):
            init=(base/"__init__.py").read_text()
            self.assertIn("from .visual_ws import visual_subscribe, visual_identity",init)
            self.assertIn("async_register_command(hass, visual_subscribe)",init)
            self.assertIn("async_register_command(hass, visual_identity)",init)
            self.assertIn('StaticPathConfig("/tablet_assist_for_alexa/visual_client.js"',init)
            self.assertTrue((base/"frontend"/"visual_client.js").is_file())
            self.assertTrue((base/"visual_ws.py").is_file())
    def test_bundle_matches_live_visual_contract(self):
        for name in ("__init__.py","visual_ws.py","frontend/visual_client.js",
                     "frontend/response_overlay.js","frontend/ambient_night.js",
                     "frontend/dashboard.js","manifest.json"):
            self.assertEqual((MAIN/name).read_bytes(),(BUNDLE/name).read_bytes(),name)
if __name__=="__main__":
    unittest.main()
