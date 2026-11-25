"""Exercise HA App settings normalization without installing Home Assistant itself.

We extract pure validation functions from the integration source and mock the
entity registry. This guards migrations and prevents unsafe destination values.
"""
import ast
import json
import re
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
HA = ROOT / "custom_components" / "tablet_assist_for_alexa"


def pure_source(path, funcs=(), variables=()):
    nodes = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in funcs:
            node.decorator_list = []
            nodes.append(node)
        elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in variables for t in node.targets):
            nodes.append(node)
    return nodes


def load_validators():
    namespace = {"ast": ast, "json": json, "re": re, "urlsplit": urlsplit,
                 "DOMAIN": "tablet_assist_for_alexa"}
    combined = [
        *pure_source(HA / "config_flow.py", ("origin", "room_map"), ("CHOICES",)),
        *pure_source(HA / "sources.py", variables=("SOURCES",)),
        *pure_source(HA / "app_settings.py",
                     ("parse_settings", "_unique_wyoming_stt", "merge_settings")),
    ]
    module = ast.fix_missing_locations(ast.Module(body=combined, type_ignores=[]))
    exec(compile(module, "<TAFA pure validation>", "exec"), namespace)
    return namespace


class Registry:
    def __init__(self, entities=None):
        self.entities = {
            e.entity_id: e for e in (entities or [])
        }

    def async_get(self, entity_id):
        return self.entities.get(entity_id)


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.funcs = load_validators()

    def sample(self, **override):
        values = {
            "piper_base": "http://192.168.1.50:5000",
            "gpu_base": "http://192.168.1.60:10502",
            "hardware_profile": "automatic",
            "live_profile": "studio",
            "conversation_mode": "intelligent",
            "mp3_profile": "announcement",
            "voice_variant": "default",
            "mp3_base": "http://192.168.1.50:5001",
            "public_audio_base": "https://tafa.example.org",
            "rooms_json": "{}",
            "sources_json": "{}",
            "cpu_stt": "",
            "gpu_stt": "",
            "llm_agent": "",
            "gpu_stt_host": "",
            "chime": False,
            "reminders_enabled": False,
            "learning_enabled": False,
            "reminder_room": "",
        }
        values.update(override)
        return values

    def test_normalization_and_sources(self):
        registry = Registry()
        data = self.funcs["parse_settings"](
            self.sample(rooms_json='{"Wohnzimmer":{"notify":"notify.echo"}}',
                        sources_json='{"solar":"sensor.pv"}'), registry)
        self.assertEqual(data["hardware_profile"], "Automatisch")
        self.assertEqual(data["live_profile"], "Studio")
        self.assertEqual(data["mp3_profile"], "Durchsage")
        self.assertEqual(data["sources"]["solar"], "sensor.pv")
        self.assertEqual(data["rooms"]["Wohnzimmer"]["notify"], "notify.echo")
        self.assertNotIn("gpu_api_key", data)

    def test_initial_migration_preserves_advanced_settings(self):
        parse = self.funcs["parse_settings"]
        merge = self.funcs["merge_settings"]
        registry = Registry()
        old = SimpleNamespace(
            data={"cpu_stt": "stt.previous",
                  "rooms": {"Wohnzimmer": {"notify": "notify.old"}},
                  "sources": {"weather": "weather.old"}},
            options={"gpu_base": "http://192.168.1.88:10502"})
        updated = merge(old, parse(self.sample(), registry), registry)
        self.assertTrue(updated["tafa_app_managed"])
        self.assertEqual(updated["cpu_stt"], "stt.previous")
        self.assertIn("Wohnzimmer", updated["rooms"])
        self.assertEqual(updated["sources"]["weather"], "weather.old")
        self.assertEqual(updated["gpu_base"], "http://192.168.1.60:10502")
        # After the first handover the App is authoritative, so clearing
        # a field in App Configuration really clears it in HA.
        second = SimpleNamespace(data=old.data, options=updated)
        cleared = merge(second, parse(self.sample(), registry), registry)
        self.assertEqual(cleared["cpu_stt"], "")
        self.assertEqual(cleared["rooms"], {})
        self.assertEqual(cleared["sources"], {})

    def test_auto_select_only_one_wyoming_stt(self):
        provider = SimpleNamespace(entity_id="stt.whisper", platform="wyoming",
                                   disabled_by=None)
        providers = Registry([provider])
        parse = self.funcs["parse_settings"]
        merge = self.funcs["merge_settings"]
        entry = SimpleNamespace(data={}, options={})
        updated = merge(entry, parse(self.sample(), providers), providers)
        self.assertEqual(updated["cpu_stt"], "stt.whisper")
        wrong = SimpleNamespace(entity_id="stt.another", platform="wyoming",
                                disabled_by=None)
        self.assertEqual(
            merge(entry, parse(self.sample(), Registry([provider, wrong])),
                  Registry([provider, wrong]))["cpu_stt"], "")

    def test_bad_urls_and_unrecognized_entities_are_rejected(self):
        parse = self.funcs["parse_settings"]
        for changes in [
            {"piper_base": "https://username:password@bad.example.org:5000"},
            {"public_audio_base": "http://not-secure.example.org"},
            {"gpu_base": "http://username:pass@host:10502"},
            {"cpu_stt": "stt.missing"},
            {"rooms_json": '{"Wohnzimmer":{"notify":"notify.echo","secret":"bad"}}'},
            {"sources_json": '{"solar":"switch.invalid"}'},
            {"llm_agent": "conversation.invalid/name"},
        ]:
            with self.subTest(changes=changes):
                with self.assertRaises((ValueError, TypeError)):
                    parse(self.sample(**changes), Registry())


if __name__ == "__main__":
    unittest.main()
