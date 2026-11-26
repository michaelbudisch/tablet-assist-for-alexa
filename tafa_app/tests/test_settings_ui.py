"""One store, validation, escaping and preservation for the TAFA Control Center."""
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings_ui import SETTINGS_FIELDS, BOOL_FIELDS, render_settings_form, render_connection_form, validate_settings_form, validate_connection_form, save_connection_form, save_app_changes
from speech_source import setup_settings_values


class SettingsUI(unittest.TestCase):
    def form(self, **changes):
        defaults = {k: "" for k in SETTINGS_FIELDS - set(BOOL_FIELDS)}
        defaults.update({"speech_mode": "local", "hardware_profile": "automatic",
                         "voice_variant": "default", "live_profile": "natural",
                         "conversation_mode": "intelligent", "mp3_profile": "natural",
                         "rooms_json": "{}", "sources_json": "{}"})
        defaults.update(changes)
        return {k: [v] for k,v in defaults.items()}

    def test_full_form_validates_and_preserves_existing_keys(self):
        form = self.form(cpu_stt="stt.cpu", gpu_stt="stt.gpu")
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
            validate_settings_form({**self.form(), "gpu_base": ["http://example.org:10502"]},{},[])
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
        self.assertIn("Sprachassistent und KI",de)
        self.assertIn("Voice assistant and AI",en)
        self.assertIn('value="stt.cpu" selected',de)
        self.assertIn("CPU &amp; &lt;Whisper&gt;",de)
        self.assertIn('id="wyoming-picker"',de)
        self.assertEqual(de.count('name="action" value="settings"'),1)
        self.assertNotIn('name="gpu_base"',de)
        self.assertNotIn('name="gpu_stt_host"',de)
        self.assertNotIn('name="mp3_base"',de)
        self.assertNotIn('name="public_audio_base"',de)

    def test_connection_form_only_edits_addresses_and_checks_values(self):
        options = {"gpu_base":"http://192.168.1.30:10502",
                   "public_audio_base":"https://tafa.example.org"}
        html = render_connection_form(options,"de","csrf",checks={"gpu_base":"ready"})
        self.assertIn('name="gpu_base"',html)
        self.assertIn('data-connection-probe="gpu_base"',html)
        self.assertIn('data-connection-probe="public_audio_base"',html)
        self.assertIn('name="action" value="connection_settings"',html)
        self.assertNotIn('name="llm_agent"',html)
        self.assertNotIn('name="rooms_json"',html)
        fields = {name:[""] for name in (
            "external_piper_base","gpu_base","gpu_stt_host","mp3_base","public_audio_base")}
        fields.update({"gpu_base":["http://192.168.1.30:10502"],
                       "public_audio_base":["https://tafa.example.org"]})
        updated = validate_connection_form(fields,{"llm_agent":"conversation.ollama"})
        self.assertEqual(updated["gpu_base"],"http://192.168.1.30:10502")
        self.assertNotIn("llm_agent",updated)
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"llm_agent":["conversation.other"]},{})
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"gpu_base":["http://8.8.8.8:10502"]},{})


if __name__=="__main__":
    unittest.main()
