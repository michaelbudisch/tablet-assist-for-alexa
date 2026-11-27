"""Pure follow-up decision tests; no Home Assistant import required."""
import importlib.util
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"custom_components"/
        "tablet_assist_for_alexa"/"followup_decision.py")
spec=importlib.util.spec_from_file_location("followup_decision",SOURCE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FollowupDecisionTest(unittest.TestCase):
    def test_intelligent_does_not_reopen_after_factual_answer(self):
        self.assertFalse(mod.wants_followup("Intelligent","Berlin ist die Hauptstadt."))
    def test_actual_question_keeps_context(self):
        self.assertTrue(mod.wants_followup("Intelligent","Welche Seite soll ich öffnen?"))
        self.assertTrue(mod.wants_followup("Intelligent","Bitte sage die gewünschte Nummer."))
    def test_generic_question_is_not_listening_invite(self):
        self.assertFalse(mod.wants_followup("Intelligent","Hast du noch weitere Fragen?"))
    def test_delegated_explicit_continue_is_honored(self):
        self.assertTrue(mod.wants_followup("Intelligent","Erledigt.",True))
    def test_manual_and_automatic_modes(self):
        self.assertFalse(mod.wants_followup("Manuell","Welche Seite soll ich öffnen?"))
        self.assertTrue(mod.wants_followup("Automatisch","Erledigt."))
if __name__=="__main__":
    unittest.main()
