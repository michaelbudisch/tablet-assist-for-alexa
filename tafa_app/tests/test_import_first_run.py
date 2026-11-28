"""Import-first setup and shared Android branding contract."""
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[2]
APP=ROOT/"tafa_app"
sys.path.insert(0,str(APP))
import server
from speech_source import choose

class SetupAndBrandTests(unittest.TestCase):
    def test_fresh_app_setup_disables_cpu_models_until_confirmed(self):
        config=(APP/"config.yaml").read_text(encoding="utf-8")
        self.assertIn("speech_mode: setup",config)
        with patch.object(server,"bootstrap",return_value=[]), \
             patch.object(server,"choose_speech_source",return_value=("setup","")), \
             patch.object(server,"_cpu_monitor") as monitor, \
             patch.object(server,"_launch_autoconfigure") as auto, \
             patch.object(server,"publish_service_address") as publish, \
             patch.object(server,"save_state") as state:
            server.startup()
        monitor.assert_not_called()
        auto.assert_not_called()
        publish.assert_not_called()
        state.assert_called_once()
        self.assertEqual(state.call_args.args[0],"awaiting_import")

    def test_confirmed_modes_start_only_selected_services(self):
        with patch.object(server,"choose_speech_source",return_value=("local","")), \
             patch.object(server,"_internal_address",return_value="http://tafa-internal:5000"), \
             patch.object(server,"_cpu_monitor") as cpu, \
             patch.object(server,"publish_service_address") as publish, \
             patch.object(server,"_launch_autoconfigure") as auto, \
             patch.object(server,"_start_import_finalizer"):
            server.activate_configured_services()
            cpu.assert_called_once()
            publish.assert_called_once_with("http://tafa-internal:5000")
            auto.assert_called_once_with("http://tafa-internal:5000","local",{})
        with patch.object(server,"load_options",return_value={"speech_mode":"external","external_piper_base":"http://10.0.0.18:5000"}), \
             patch.object(server,"choose_speech_source",return_value=("external","http://10.0.0.18:5000")), \
             patch.object(server,"_cpu_monitor") as cpu, \
             patch.object(server,"publish_service_address") as publish, \
             patch.object(server,"_launch_autoconfigure") as auto, \
             patch.object(server,"_start_import_finalizer"):
            server.activate_configured_services()
            cpu.assert_not_called()
            publish.assert_called_once_with("http://10.0.0.18:5000")
            auto.assert_called_once_with("http://10.0.0.18:5000","external",{"speech_mode":"external","external_piper_base":"http://10.0.0.18:5000"})

    def test_saved_entries_enable_later_entity_resolution(self):
        records={
            "worker":{"kind":"gpu_worker","host":"10.0.0.4",
                      "entries":{"wyoming_stt":"gpu-entry","ollama":"llm-entry"},
                      "expected":{"wyoming_stt":True,"ollama":True}},
            "speech":{"kind":"speech_server","host":"10.0.0.8",
                      "entries":{"wyoming_stt":"cpu-entry"},
                      "expected":{"wyoming_stt":True,"ollama":False}}
        }
        with patch.object(server,"load_records",return_value=records):
            mapped=server._tracked_profiles()
        self.assertEqual(mapped["gpu_worker"]["ollama"],"llm-entry")
        self.assertTrue(mapped["gpu_worker"]["expected"]["ollama"])
        self.assertFalse(mapped["speech_server"]["expected"]["ollama"])
        self.assertEqual(mapped["speech_server"]["wyoming_stt"],"cpu-entry")

    def test_finish_delayed_entities_without_recreating_integrations(self):
        with patch.object(server,"_tracked_profiles",return_value={
                  "gpu_worker":{"wyoming_stt":"entry","expected":{"wyoming_stt":True,"ollama":False}}}), \
             patch.object(server,"load_records",return_value={"test-device":{
                 "kind":"gpu_worker","provision_pending":False}}), \
             patch.object(server,"resolve_import_entities",return_value={
                 "entities":{"gpu_stt":"stt.gpu_1"},"pending":[]}) as resolve, \
             patch.object(server,"load_options",return_value={"gpu_stt":""}), \
             patch.object(server,"save_app_changes") as save, \
             patch.object(server,"choose_speech_source",return_value=("local","")), \
             patch.object(server,"_internal_address",return_value="http://tafa-internal:5000"), \
             patch.object(server,"setup_settings",return_value={"gpu_stt":"stt.gpu_1"}), \
             patch.object(server,"sync_app_configuration") as sync, \
             patch.object(server,"TOKEN","private-test-token"):
            server._complete_imports()
        self.assertEqual(resolve.call_count,1)
        save.assert_called_once_with("private-test-token",{"gpu_stt":"stt.gpu_1"},import_kind="gpu_worker")
        sync.assert_called_once()

    def test_delayed_gpu_registration_clears_cpu_alias_for_same_entity(self):
        with patch.object(server,"_tracked_profiles",return_value={
                  "gpu_worker":{"wyoming_stt":"gpu-entry",
                                "expected":{"wyoming_stt":True,"ollama":False}}}), \
             patch.object(server,"load_records",return_value={"worker":{
                 "kind":"gpu_worker","provision_pending":False}}), \
             patch.object(server,"resolve_import_entities",return_value={
                 "entities":{"gpu_stt":"stt.gpu_whisper"},"pending":[]}), \
             patch.object(server,"load_options",return_value={
                 "cpu_stt":"stt.gpu_whisper","gpu_stt":""}), \
             patch.object(server,"save_app_changes") as save, \
             patch.object(server,"choose_speech_source",return_value=("local","")), \
             patch.object(server,"_internal_address",return_value="http://tafa-internal:5000"), \
             patch.object(server,"setup_settings",return_value={
                 "cpu_stt":"","gpu_stt":"stt.gpu_whisper"}), \
             patch.object(server,"sync_app_configuration"), \
             patch.object(server,"TOKEN","test-internal-token"):
            server._complete_imports()
        save.assert_called_once_with(
            "test-internal-token",{"gpu_stt":"stt.gpu_whisper","cpu_stt":""},import_kind="gpu_worker")

    def test_delayed_resolution_repairs_existing_saved_duplicate(self):
        with patch.object(server,"_tracked_profiles",return_value={
                  "gpu_worker":{"wyoming_stt":"gpu-entry",
                                "expected":{"wyoming_stt":True,"ollama":False}}}), \
             patch.object(server,"load_records",return_value={"worker":{
                 "kind":"gpu_worker","provision_pending":False}}), \
             patch.object(server,"resolve_import_entities",return_value={
                 "entities":{"gpu_stt":"stt.gpu_whisper"},"pending":[]}), \
             patch.object(server,"load_options",return_value={
                 "cpu_stt":"stt.gpu_whisper","gpu_stt":"stt.gpu_whisper"}), \
             patch.object(server,"save_app_changes") as save, \
             patch.object(server,"choose_speech_source",return_value=("local","")), \
             patch.object(server,"_internal_address",return_value="http://tafa-internal:5000"), \
             patch.object(server,"setup_settings",return_value={
                 "cpu_stt":"","gpu_stt":"stt.gpu_whisper"}), \
             patch.object(server,"sync_app_configuration"), \
             patch.object(server,"TOKEN","test-internal-token"):
            server._complete_imports()
        save.assert_called_once_with("test-internal-token",{"cpu_stt":""},import_kind="gpu_worker")

    def test_import_will_validate_repaired_proposed_options(self):
        source=(APP/"server.py").read_text(encoding="utf-8")
        self.assertIn("configure(piper,setup_settings_values(proposed))",source)
        self.assertIn("current,proposed_options(manifest,current),manifest",source)

    def test_android_launcher_vector_is_identical_on_both_web_surfaces(self):
        original=(ROOT/"android/app/src/main/res/drawable/ic_launcher_foreground.xml").read_text()
        geometry=re.findall(r'android:pathData="([^"]+)"',original)
        self.assertEqual(len(geometry),2)
        files=(APP/"brand.svg",
              ROOT/"custom_components/tablet_assist_for_alexa/frontend/brand.svg",
              APP/"bundle/tablet_assist_for_alexa/frontend/brand.svg")
        content=[file.read_text(encoding="utf-8") for file in files]
        self.assertEqual(content[0],content[1])
        self.assertEqual(content[1],content[2])
        for path in geometry:
            self.assertIn(path,content[0])
        self.assertIn("#1AD6F5",content[0])
        self.assertIn("#65E2CD",content[0])
        ElementTree.fromstring(content[0])
        self.assertIn("brand.svg",(APP/"Dockerfile").read_text())
        # The integrated dashboard no longer has a duplicate logo toolbar.
        # The brand asset remains registered and available for other TAFA UI.
        self.assertIn("/tablet_assist_for_alexa/brand.svg",
                      (ROOT/"custom_components/tablet_assist_for_alexa/__init__.py").read_text())
        self.assertNotIn('className="toolbar"',
                         (ROOT/"custom_components/tablet_assist_for_alexa/frontend/panel.js").read_text())
        self.assertIn("assets/brand.svg",(APP/"control_center_view.py").read_text())
        self.assertIn("img-src 'self'",(APP/"server.py").read_text())


if __name__=="__main__":
    unittest.main()
