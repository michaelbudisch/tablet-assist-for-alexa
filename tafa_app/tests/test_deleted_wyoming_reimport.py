"""Regression: reimport after removing Wyoming via HA Devices & Services.

Extract pure config-entry matching function from the mirrored integration to
exercise the actual implementation without requiring Home Assistant in App CI.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"custom_components/tablet_assist_for_alexa/ha_provision.py"
MIRROR=ROOT/"tafa_app/bundle/tablet_assist_for_alexa/ha_provision.py"


def load_matcher():
    source=BASE.read_text(encoding="utf-8")
    tree=ast.parse(source,filename=str(BASE))
    fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef)
            and node.name=="_associated_entry")
    compiled=compile(ast.Module(body=[fn],type_ignores=[]),str(BASE),"exec")
    scope={}
    exec(compiled,scope)
    return scope["_associated_entry"]


def entry(domain,entry_id,host="10.1.2.3",port=10300):
    data={"host":host,"port":port} if domain=="wyoming" else {"url":f"http://{host}:11434"}
    return SimpleNamespace(domain=domain,entry_id=entry_id,data=data)


class ConfigEntries:
    def __init__(self,entries):
        self.entries=entries
    def async_entries(self,domain):
        return [e for e in self.entries if e.domain==domain]


class ReimportAfterDeletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher=staticmethod(load_matcher())
        cls.mirrored_source=MIRROR.read_text(encoding="utf-8")

    def setUp(self):
        self.match=load_matcher()

    def hass(self,*entries):
        return SimpleNamespace(config_entries=ConfigEntries(entries))

    def test_integration_bundle_and_repo_match(self):
        self.assertEqual(BASE.read_text(encoding="utf-8"),self.mirrored_source)

    def test_deleted_wyoming_mapping_causes_clean_new_registration(self):
        # Old ID was persisted in TAFA, but user explicitly deleted entry.
        result=self.match(self.hass(),"wyoming","10.1.2.3","deleted-entry",10300)
        self.assertEqual(result,(None,False))

    def test_deleted_ollama_mapping_can_be_recreated(self):
        result=self.match(self.hass(),"ollama","10.1.2.3","old-ollama-id")
        self.assertEqual(result,(None,False))

    def test_same_endpoint_reuses_entry_even_if_mapping_is_stale(self):
        current=entry("wyoming","new-entry")
        self.assertEqual(self.match(self.hass(current),"wyoming","10.1.2.3",
                                    "deleted-entry",10300),(current,False))

    def test_tracked_entry_with_new_ip_can_be_reconfigured(self):
        old=entry("wyoming","still-present","10.1.2.4")
        self.assertEqual(self.match(self.hass(old),"wyoming","10.1.2.3",
                                    "still-present",10300),(old,True))

    def test_unrelated_entries_never_reconfigured_or_deleted(self):
        unrelated=entry("wyoming","unrelated","10.1.2.5")
        self.assertEqual(self.match(self.hass(unrelated),"wyoming","10.1.2.3",
                                    "deleted-entry",10300),(None,False))

    def test_multiple_same_endpoint_matches_require_manual_review(self):
        entries=[entry("wyoming","first"),entry("wyoming","second")]
        with self.assertRaisesRegex(ValueError,"Multiple integration entries"):
            self.match(self.hass(*entries),"wyoming","10.1.2.3","deleted-entry",10300)

    def test_error_message_propagates_to_app(self):
        app=(ROOT/"tafa_app/auto_setup.py").read_text(encoding="utf-8")
        self.assertIn('error.get("message")',app)
        self.assertIn('TAFA HA provisioning unavailable: ',app)


if __name__=="__main__":
    unittest.main()
