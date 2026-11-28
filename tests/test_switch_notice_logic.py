"""Regression tests for conservative native Assist switch target matching."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"custom_components"/"tablet_assist_for_alexa"/"switch_notice_logic.py"
spec=importlib.util.spec_from_file_location("tafa_switch_notice_logic",FILE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SwitchNoticeLogicTests(unittest.TestCase):
    def test_explicit_entity(self):
        self.assertEqual(mod.extract_targets("light","turn_on",{"entity_id":"light.buro_led"}),("light.buro_led",))
        self.assertEqual(mod.expected_state("turn_on","off"),"on")
        self.assertEqual(mod.expected_state("turn_off","on"),"off")
        self.assertEqual(mod.expected_state("toggle","on"),"off")

    def test_multi_and_wrong_targets(self):
        self.assertEqual(mod.extract_targets("homeassistant","turn_off",{"entity_id":["light.a","switch.b"]}),("light.a","switch.b"))
        self.assertEqual(mod.extract_targets("light","turn_on",{"entity_id":"switch.a"}),())
        self.assertEqual(mod.extract_targets("homeassistant","turn_on",{"area_id":"office"}),())
        self.assertEqual(mod.extract_targets("light","toggle",{"entity_id":"light.a,switch.b"}),())
        self.assertEqual(mod.extract_targets("light","turn_on",{"entity_id":"light.a,light.b"}),("light.a","light.b"))
        self.assertEqual(mod.extract_targets("light","turn_on",{"entity_id":["light."+str(i) for i in range(7)]}),())
        self.assertEqual(mod.extract_targets("light","turn_on",{"entity_id":"script.tafa_geraet_schalten"}),())
        self.assertEqual(mod.extract_targets("light","turn_on",{"target":{"entity_id":["light.a"]}}),("light.a",))

    def test_confirmed_native_state_transitions(self):
        # The observed native light intent changed a root-user-owned entity
        # without the initial explicit service-hook notification.
        self.assertTrue(mod.confirmed_transition("light.buro_arbeitszimmer_led","off","on"))
        self.assertTrue(mod.confirmed_transition("light.buro_arbeitszimmer_led","on","off"))
        self.assertFalse(mod.confirmed_transition("light.buro_arbeitszimmer_led","on","on"))
        self.assertFalse(mod.confirmed_transition("light.buro_arbeitszimmer_led","unknown","on"))
        self.assertFalse(mod.confirmed_transition("sensor.energy","off","on"))
        self.assertFalse(mod.confirmed_transition("light.office","off","unavailable"))

    def test_native_android_detection_routing(self):
        self.assertEqual(mod.reported_native_wake("detected: Jarvis", "Jarvis"), "Jarvis")
        self.assertEqual(mod.reported_native_wake("detected: Hey Jarvis", "Jarvis"), "Hey Jarvis")
        self.assertEqual(mod.reported_native_wake("detected: Alexa", "Alle drei"), "Alexa")
        for status, selected in [
            ("listening: jarvis", "Jarvis"),
            ("native_processing", "Jarvis"),
            ("detected: Alexa", "Jarvis"),
            ("detected: unknown", "Alle drei"),
            ("detected: Jarvis", "Alexa"),
            ("detected:", "Jarvis"),
        ]:
            self.assertIsNone(mod.reported_native_wake(status, selected))

    def test_only_confirmed_state_changes_publish_native_cards(self):
        source = (ROOT/"custom_components"/"tablet_assist_for_alexa"
                  /"switch_intent_bridge.py").read_text()
        self.assertIn("EVENT_STATE_CHANGED, state_changed", source)
        self.assertNotIn("EVENT_CALL_SERVICE", source)

    def test_pair_and_one_service_context(self):
        wake={"user_id":"room-user","at":20,"context_id":None}
        self.assertTrue(mod.eligible_wake(wake,"room-user",25,"intent-123"))
        self.assertFalse(mod.eligible_wake(wake,"admin-user",25,"intent-123"))
        self.assertFalse(mod.eligible_wake(wake,"room-user",50,"intent-123"))
        wake["context_id"]="intent-123"
        self.assertTrue(mod.eligible_wake(wake,"room-user",25,"intent-123"))
        self.assertFalse(mod.eligible_wake(wake,"room-user",25,"other-context"))


if __name__=="__main__":
    unittest.main()
