"""One store, validation, escaping and preservation for the TAFA Control Center."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings_ui import FORM_FIELDS, BOOL_FIELDS, render_settings_form, validate_settings_form
from speech_source import setup_settings_values


class SettingsUI(unittest.TestCase):
    def form(self, **changes):
        defaults = {k: "" for k in FORM_FIELDS - set(BOOL_FIELDS)}
        defaults.update({"speech_mode": "local", "hardware_profile": "automatic",
                         "voice_variant": "default", "live_profile": "natural",
                         "conversation_mode": "intelligent", "mp3_profile": "natural",
                         "rooms_json": "{}", "sources_json": "{}"})
        defaults.update(changes)
        return {k: [v] for k,v in defaults.items()}

    def test_full_form_validates_and_preserves_existing_keys(self):
        form = self.form(cpu_stt="stt.cpu", gpu_stt="stt.gpu",
                         gpu_base="http://192.168.1.30:10502")
        current = {"custom_future_setting": "preserve"}
        update = validate_settings_form(form,current,[{"id":"stt.cpu"},{"id":"stt.gpu"}])
        self.assertEqual(update["cpu_stt"],"stt.cpu")
        self.assertEqual({**current,**update}["custom_future_setting"],"preserve")
        self.assertFalse(update["chime"])

    def test_no_invalid_or_unregistered_settings(self):
        with self.assertRaises(ValueError):
            validate_settings_form(self.form(speech_mode="external"),{},[])
        with self.assertRaises(ValueError):
            validate_settings_form(self.form(cpu_stt="stt.fabricated"),{},[])
        with self.assertRaises(ValueError):
            validate_settings_form(self.form(gpu_base="http://example.org:10502"),{},[])
        with self.assertRaises(ValueError):
            validate_settings_form(self.form(rooms_json="{broken"),{},[])
        with self.assertRaises(ValueError):
            validate_settings_form({"csrf":["token"]},{},[])

    def test_single_page_bilingual_safe_escaping(self):
        options = {"cpu_stt":"stt.cpu","gpu_stt":"", "llm_agent":"conversation.ollama",
                   "rooms_json":"{}", "sources_json":"{}", "speech_mode":"local"}
        rows = [{"id":"stt.cpu","name":"CPU & <Whisper>"}]
        de=render_settings_form(options,rows,"de","csrf","1 detected")
        en=render_settings_form(options,rows,"en","csrf","1 detected")
        self.assertIn("Einstellungen – zentral verwalten",de)
        self.assertIn("Settings – one place",en)
        self.assertIn('value="stt.cpu" selected',de)
        self.assertIn("CPU &amp; &lt;Whisper&gt;",de)
        self.assertIn('id="wyoming-picker"',de)
        self.assertEqual(de.count('name="action" value="settings"'),1)


if __name__=="__main__":
    unittest.main()
