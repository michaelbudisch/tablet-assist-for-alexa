"""Static distribution contract for the optional ambient calendar."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"custom_components"/"tablet_assist_for_alexa"
BUNDLE=ROOT/"tafa_app"/"bundle"/"tablet_assist_for_alexa"
class AmbientCalendarTest(unittest.TestCase):
    def test_same_optional_module_in_both_packages(self):
        for f in ("frontend/ambient_overview.js","frontend/ambient_night.js","__init__.py"):
            self.assertEqual((MAIN/f).read_bytes(),(BUNDLE/f).read_bytes())
    def test_no_direct_google_token_or_browser_microphone(self):
        js=(MAIN/"frontend/ambient_overview.js").read_text()
        self.assertIn('service:"get_events"',js)
        self.assertIn("calendar.familie",js)
        self.assertNotIn("getUserMedia",js)
        self.assertIn("hz-overview-construct",js)
        self.assertIn("hz-overview-cell-in",js)
        self.assertIn("hz-overview-edge",js)
        self.assertIn('class="edge-n"',js)
        self.assertNotIn('class="top"',js)
        self.assertIn("playBeam",js)
        self.assertIn("prefers-reduced-motion",js)
        self.assertIn("cancelAnimationFrame(beamFrame)",js)
        self.assertIn("entityEvents=id=>",js)
        self.assertIn('service:"get_events"',js)
        self.assertIn('card.h.callApi("GET",uri)',js)
        self.assertIn("mergeEvents(received||[],entityEvents(id))",js)
        self.assertIn("hz-overview-particles",js)
        self.assertIn("Shooting stars run FROM sphere nodes",js)
        self.assertIn("Nodes appear only after",js)
        self.assertIn('service:"get_forecasts"',js)
        self.assertIn("validPower=e=>",js)
        self.assertIn("hz-overview-forecast",js)
        self.assertIn("hz-overview-energy",js)
        self.assertIn("hz-overview-bottom",js)
        self.assertIn("<span>SO</span><span>MO</span>",js)
        self.assertIn("background:transparent!important",js)
        self.assertIn("data-next-event",js)
        self.assertNotIn("subscribeEvents",js)
    def test_optional_resource_is_registered(self):
        src=(MAIN/"__init__.py").read_text()
        self.assertIn('StaticPathConfig("/tablet_assist_for_alexa/ambient_overview.js"',src)
if __name__=="__main__":
    unittest.main()
