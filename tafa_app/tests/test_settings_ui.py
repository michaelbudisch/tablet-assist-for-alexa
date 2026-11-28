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
                         })
        defaults.update(changes)
        return {k: [v] for k,v in defaults.items()}

    def test_full_form_validates_and_preserves_existing_keys(self):
        form = self.form()
        current = {"custom_future_setting": "preserve",
                   "cpu_stt":"stt.cpu","gpu_stt":"stt.gpu",
                   "llm_agent":"conversation.ollama"}
        update = validate_settings_form(form,current,[{"id":"stt.cpu"},{"id":"stt.gpu"}])
        self.assertNotIn("cpu_stt",update)
        self.assertNotIn("gpu_stt",update)
        self.assertNotIn("llm_agent",update)
        self.assertEqual({**current,**update}["cpu_stt"],"stt.cpu")
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
        snapshots=iter([latest,{**latest,"cpu_stt":"","gpu_base":requested["gpu_base"]}])
        with patch("settings_ui.load_supervisor_options",side_effect=lambda token: next(snapshots)), \
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
        snapshots=iter([latest,{**latest,"gpu_stt":"stt.worker_new"}])
        with patch("settings_ui.load_supervisor_options",side_effect=lambda token: next(snapshots)), \
             patch("settings_ui.urllib.request.urlopen",return_value=response) as urlopen:
            save_app_changes("internal-test-token",
                             {"gpu_stt":"stt.worker_new"},import_kind="gpu_worker")
        opts=json.loads(urlopen.call_args.args[0].data)["options"]
        self.assertEqual(opts["cpu_stt"],"stt.real_cpu")
        self.assertEqual(opts["gpu_stt"],"stt.worker_new")

    def test_manual_save_still_rejects_duplicate_roles(self):
        with patch("settings_ui.load_supervisor_options",
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
        self.assertNotIn('name="cpu_stt"',de)
        self.assertNotIn('name="gpu_stt"',de)
        self.assertNotIn('name="llm_agent"',de)
        panel=render_connection_form(options,"de","csrf",wyoming=rows)
        self.assertIn('value="stt.cpu" selected',panel)
        self.assertIn("CPU &amp; &lt;Whisper&gt;",panel)
        self.assertIn('name="cpu_stt"',panel)
        self.assertIn('name="gpu_stt"',panel)
        self.assertEqual(de.count('name="action" value="settings"'),1)
        self.assertNotIn('name="gpu_base"',de)
        self.assertNotIn('name="gpu_stt_host"',de)
        self.assertNotIn('name="mp3_base"',de)
        self.assertNotIn('name="public_audio_base"',de)

    def test_connection_form_groups_services_and_wyoming_choices(self):
        options = {"gpu_base":"http://192.168.1.30:10502",
                   "gpu_stt_host":"192.168.1.30","gpu_stt":"stt.gpu",
                   "cpu_stt":"stt.cpu","llm_agent":"conversation.ollama",
                   "public_audio_base":"https://tafa.example.org"}
        providers=[{"id":"stt.gpu","name":"GPU Whisper"},
                   {"id":"stt.cpu","name":"CPU Whisper"}]
        page = render_connection_form(options,"de","csrf",
                                      checks={"gpu_base":"ready","gpu_stt_host":"reachable"},
                                      wyoming=providers,
                                      latest={"backend":"zusatzrechner","duration_ms":430})
        for name in ("gpu_stt_host","gpu_base","gpu_stt","llm_agent",
                     "external_piper_base","cpu_stt","mp3_base","public_audio_base"):
            self.assertIn('name="'+name+'"',page)
        self.assertLess(page.index("1 · GPU / KI"),page.index("2 · CPU-Fallback"))
        self.assertLess(page.index("2 · CPU-Fallback"),page.index("3 · Alexa"))
        self.assertIn('value="stt.gpu" selected',page)
        self.assertIn('value="stt.cpu" selected',page)
        self.assertIn("0,8 Sekunden",page)
        self.assertIn("Letzte Spracherkennung",page)
        self.assertIn('name="action" value="connection_settings"',page)
        self.assertNotIn('name="hardware_profile"',page)
        self.assertNotIn('name="rooms_json"',page)

    def test_connection_save_validates_entity_roles_and_preserves_unrelated(self):
        current = {"hardware_profile":"automatic",
                   "conversation_mode":"intelligent","rooms_json":"{}",
                   "sources_json":"{}","speech_mode":"local",
                   "custom_setting":"unchanged"}
        fields = {name:[""] for name in (
            "gpu_stt_host","gpu_base","gpu_stt","llm_agent",
            "external_piper_base","cpu_stt","mp3_base","public_audio_base")}
        fields.update({"gpu_stt_host":["192.168.1.30"],
                       "gpu_base":["http://192.168.1.30:10502"],
                       "gpu_stt":["stt.gpu"],"cpu_stt":["stt.cpu"],
                       "llm_agent":["conversation.ollama"]})
        available=[{"id":"stt.gpu"},{"id":"stt.cpu"}]
        changes=validate_connection_form(fields,current,available)
        self.assertEqual(changes["gpu_stt_host"],"192.168.1.30")
        self.assertEqual(changes["llm_agent"],"conversation.ollama")
        self.assertNotIn("hardware_profile",changes)
        self.assertEqual({**current,**changes}["custom_setting"],"unchanged")
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"gpu_stt":["stt.cpu"]},current,available)
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"gpu_stt":["stt.invented"]},current,available)
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"gpu_base":["http://8.8.8.8:10502"]},current,available)
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"conversation_mode":["manual"]},current,available)
        with self.assertRaises(ValueError):
            validate_connection_form({**fields,"llm_agent":["sensor.incorrect"]},current,available)

    def test_existing_wyoming_selection_survives_temporary_discovery_failure(self):
        current={"gpu_stt":"stt.working_gpu","cpu_stt":"stt.working_cpu"}
        fields={key:[""] for key in (
            "gpu_stt_host","gpu_base","gpu_stt","llm_agent",
            "external_piper_base","cpu_stt","mp3_base","public_audio_base")}
        fields["gpu_stt"]=["stt.working_gpu"]
        fields["cpu_stt"]=["stt.working_cpu"]
        changes=validate_connection_form(fields,current,[])
        self.assertEqual(changes["gpu_stt"],"stt.working_gpu")
        self.assertEqual(changes["cpu_stt"],"stt.working_cpu")


if __name__=="__main__":
    unittest.main()
