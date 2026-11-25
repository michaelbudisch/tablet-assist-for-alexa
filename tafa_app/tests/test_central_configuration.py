"""App Configuration owns all options; validate before applying to HA Core."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from speech_source import setup_settings


class CentralConfigurationTests(unittest.TestCase):
    def parse(self, opts):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "options.json"
            p.write_text(json.dumps(opts, ensure_ascii=False), encoding="utf-8")
            return setup_settings(p)

    def test_optional_advanced_configuration_is_validated(self):
        params = {
            "cpu_stt": "stt.faster_whisper",
            "gpu_stt": "stt.gpu_whisper",
            "gpu_stt_host": "192.168.1.60",
            "llm_agent": "conversation.ollama",
            "conversation_mode": "intelligent",
            "mp3_base": "http://192.168.1.50:5001",
            "public_audio_base": "https://tafa.example.org",
            "rooms_json": '{"Wohnzimmer":{"notify":"notify.echo_wohnzimmer"}}',
            "sources_json": '{"weather":"weather.home","solar":"sensor.pv_power"}',
            "learning_enabled": True,
            "reminders_enabled": True,
            "reminder_room": "Wohnzimmer",
        }
        result = self.parse(params)
        self.assertEqual(result["cpu_stt"], "stt.faster_whisper")
        self.assertEqual(result["llm_agent"], "conversation.ollama")
        self.assertEqual(json.loads(result["rooms_json"])["Wohnzimmer"]["notify"],
                         "notify.echo_wohnzimmer")
        self.assertEqual(json.loads(result["sources_json"])["solar"], "sensor.pv_power")
        self.assertTrue(result["reminders_enabled"])
        self.assertNotIn("gpu_api_key", result)
        self.assertNotIn("mp3_api_key", result)

    def test_rejects_malformed_data_and_unknown_ha_entities(self):
        bad = [
            {"sources_json": "not json"},
            {"sources_json": '{"secret":"sensor.thing"}'},
            {"sources_json": '{"weather":"sensor.temperature"}'},
            {"rooms_json": '{"unknown":{"notify":"notify.tv"}}'},
            {"rooms_json": '{"Wohnzimmer":{"notify":"sensor.temperature"}}'},
            {"cpu_stt": "stt.bad/name"},
            {"cpu_stt": "stt.same", "gpu_stt": "stt.same"},
            {"gpu_stt_host": "https://external.example.org"},
            {"reminder_room": "Kinderzimmer"},
            {"learning_enabled": "true"},
        ]
        for options in bad:
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    self.parse(options)

    def test_audio_rooms_require_private_generator_and_public_https(self):
        with self.assertRaises(ValueError):
            self.parse({"rooms_json": '{"Wohnzimmer":{"notify":"notify.echo"}}'})
        self.assertEqual(
            self.parse({"sources_json": "{}", "rooms_json": "{}"})["sources_json"], "{}")


if __name__ == "__main__":
    unittest.main()
