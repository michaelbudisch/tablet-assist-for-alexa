"""One store, validation, escaping and preservation for the TAFA Control Center."""
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings_ui import FORM_FIELDS, BOOL_FIELDS, render_settings_form, validate_settings_form, save_app_changes
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

    def test_import_save_repairs_latest_supervisor_stt_collision(self):
        # Regression: preview used older settings; a concurrent update (or
        # a pre-existing previous import) leaves equal CPU/GPU IDs in the
        # Supervisor file just before save_app_changes re-reads the store.
        latest={"cpu_stt":"stt.worker_gpu","gpu_stt":"stt.worker_gpu",
                "hardware_profile":"automatic","custom_setting":"keep"}
        requested={"gpu_base":"http://10.2.3.4:10502"}
        response=MagicMock()
        response.status=200
        response.read.return_value=b'{"result":"ok"}'
        response.__enter__.return_value=response
        with patch("settings_ui.load_options",return_value=latest), \
             patch("settings_ui.urllib.request.urlopen",return_value=response) as urlopen:
            changed=save_app_changes("internal-test-token",requested,
                                     import_kind="gpu_worker")
        self.assertEqual(changed["cpu_stt"],"")
        data=json.loads(urlopen.call_args.args[0].data)
        stored=data["options"]
        self.assertEqual(stored["cpu_stt"],"")
        self.assertEqual(stored["gpu_stt"],"stt.worker_gpu")
        self.assertEqual(stored["gpu_base"],"http://10.2.3.4:10502")
        self.assertEqual(stored["custom_setting"],"keep")
        self.assertEqual(latest["cpu_stt"],"stt.worker_gpu")

    def test_import_save_keeps_distinct_cpu_provider(self):
        latest={"cpu_stt":"stt.real_cpu","gpu_stt":"stt.worker_gpu"}
        response=MagicMock(status=200)
        response.status=200
        response.read.return_value=b'{"result":"ok"}'
        response.__enter__.return_value=response
        with patch("settings_ui.load_options",return_value=latest), \
             patch("settings_ui.urllib.request.urlopen",return_value=response) as urlopen:
            save_app_changes("internal-test-token",
                             {"gpu_stt":"stt.worker_new"},import_kind="gpu_worker")
        opts=json.loads(urlopen.call_args.args[0].data)["options"]
        self.assertEqual(opts["cpu_stt"],"stt.real_cpu")
        self.assertEqual(opts["gpu_stt"],"stt.worker_new")

    def test_manual_save_still_rejects_duplicate_roles(self):
        with patch("settings_ui.load_options",
                   return_value={"cpu_stt":"stt.same","gpu_stt":"stt.same"}), \
             patch("settings_ui.urllib.request.urlopen") as request:
            with self.assertRaisesRegex(ValueError,"CPU and GPU Wyoming"):
                save_app_changes("internal-test-token",{},import_kind=None)
            request.assert_not_called()

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
