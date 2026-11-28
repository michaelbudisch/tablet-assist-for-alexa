"""Regression tests for TAFA settings and voice-variant persistence.

Run with: python -m unittest discover -s tafa_app/tests -p 'test_*.py'
"""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import settings_ui  # noqa: E402
import speech_source  # noqa: E402


class _Response(io.BytesIO):
    def __init__(self, payload):
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.status = 200


class VoiceVariantPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.options = {
            "speech_mode": "external",
            "external_piper_base": "http://192.168.1.50:5000",
            "hardware_profile": "automatic",
            "voice_variant": "default",
            "live_profile": "studio",
            "conversation_mode": "intelligent",
            "mp3_profile": "natural",
            "rooms_json": "{}",
            "sources_json": "{}",
            "search_base": "",
            "mp3_base": "",
            "public_audio_base": "",
            "family_name_man": "",
            "family_name_woman": "",
            "family_name_child": "",
            "cpu_stt": "",
            "gpu_stt": "",
            "gpu_stt_host": "",
            "llm_agent": "",
            "reminder_room": "",
            "chime": False,
            "learning_enabled": False,
            "reminders_enabled": False,
        }

    def _fields(self, variant):
        values = {
            key: [str(self.options.get(key, ""))]
            for key in settings_ui.SETTINGS_FIELDS - set(settings_ui.BOOL_FIELDS)
        }
        values["voice_variant"] = [variant]
        return values

    def test_supervisor_read_uses_saved_values(self):
        with patch.object(speech_source.HTTP, "open",
                          return_value=_Response({"result": "ok", "data": {"options": self.options}})):
            saved = speech_source.load_supervisor_options("test-token")
        self.assertEqual(saved["voice_variant"], "default")

    def test_selected_voice_renders_as_selected_not_default(self):
        selected = {**self.options, "voice_variant": "3"}
        html = settings_ui.render_settings_form(selected, [], "de", "csrf", "")
        self.assertIn('value="3" selected>3</option>', html)
        self.assertNotIn('value="default" selected>Standard</option>', html)

    def test_save_verifies_snapshot_and_preserves_other_options(self):
        selected = {**self.options, "voice_variant": "2"}
        get_results = iter([
            _Response({"result": "ok", "data": {"options": self.options}}),
            _Response({"result": "ok", "data": {"options": selected}}),
        ])
        posted = []

        def post(request, timeout):
            posted.append(json.loads(request.data))
            return _Response({"result": "ok"})

        with patch.object(speech_source.HTTP, "open",
                          side_effect=lambda *args, **kwargs: next(get_results)), \
             patch.object(settings_ui.urllib.request, "urlopen", side_effect=post):
            saved = settings_ui.save_settings_form("test-token", self._fields("2"), [])
        self.assertEqual(saved["voice_variant"], "2")
        self.assertEqual(posted[0]["options"]["voice_variant"], "2")
        self.assertEqual(posted[0]["options"]["live_profile"], "studio")

    def test_save_does_not_claim_success_if_variant_was_not_persisted(self):
        with patch.object(speech_source.HTTP, "open",
                          side_effect=lambda *args, **kwargs: _Response({"result": "ok", "data": {"options": self.options}})), \
             patch.object(settings_ui.urllib.request, "urlopen",
                          side_effect=lambda *args, **kwargs: _Response({"result": "ok"})):
            with self.assertRaisesRegex(RuntimeError, "not persisted"):
                settings_ui.save_settings_form("test-token", self._fields("3"), [])


if __name__ == "__main__":
    unittest.main()
