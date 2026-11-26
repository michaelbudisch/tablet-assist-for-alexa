"""Regression: never reject a new Ollama ConversationEntity before first turn."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/"custom_components"/"tablet_assist_for_alexa"/"conversation.py"


def load_agent_check():
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)
              and n.name=="_agent_is_usable")
    ns={}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 str(SOURCE),"exec"),ns)
    return ns["_agent_is_usable"]


class OllamaAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.check=load_agent_check()
        self.agent="conversation.ollama_conversation"
        self.self_id="conversation.tablet_assist_gesprachsrouter"

    def test_configured_oil_bypasses_obsolete_ha_sentence_trigger(self):
        source=SOURCE.read_text(encoding="utf-8")
        self.assertIn('prefer_tafa_oil = (',source)
        self.assertIn('classify(user_input.text) == "heizoel"',source)
        self.assertIn('self._local_data.sources.get("heizoel")',source)
        self.assertIn('if handler is not None and not prefer_tafa_oil and not prefer_tafa_search:',source)

    def test_unknown_is_the_normal_state_before_first_message(self):
        self.assertTrue(self.check(self.agent,SimpleNamespace(state="unknown"),self.self_id))

    def test_last_used_timestamp_is_usable(self):
        self.assertTrue(self.check(self.agent,
            SimpleNamespace(state="2026-11-25T12:04:00+00:00"),self.self_id))

    def test_unavailable_agent_is_rejected(self):
        self.assertFalse(self.check(self.agent,SimpleNamespace(state="unavailable"),self.self_id))

    def test_unregistered_or_self_reference_is_rejected(self):
        self.assertFalse(self.check(self.agent,None,self.self_id))
        self.assertFalse(self.check(self.self_id,SimpleNamespace(state="unknown"),self.self_id))
        self.assertFalse(self.check("",SimpleNamespace(state="unknown"),self.self_id))


if __name__=="__main__":
    unittest.main()
