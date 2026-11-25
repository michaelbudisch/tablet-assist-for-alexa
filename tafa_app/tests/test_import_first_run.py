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
            auto.assert_called_once_with("http://tafa-internal:5000","local")
        with patch.object(server,"choose_speech_source",return_value=("external","http://10.0.0.18:5000")), \
             patch.object(server,"_cpu_monitor") as cpu, \
             patch.object(server,"publish_service_address") as publish, \
             patch.object(server,"_launch_autoconfigure") as auto, \
             patch.object(server,"_start_import_finalizer"):
            server.activate_configured_services()
            cpu.assert_not_called()
            publish.assert_called_once_with("http://10.0.0.18:5000")
            auto.assert_called_once_with("http://10.0.0.18:5000","external")

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
        save.assert_called_once_with("private-test-token",{"gpu_stt":"stt.gpu_1"})
        sync.assert_called_once()

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
        self.assertIn("/tablet_assist_for_alexa/brand.svg",
                      (ROOT/"custom_components/tablet_assist_for_alexa/frontend/panel.js").read_text())
        self.assertIn("assets/brand.svg",(APP/"control_center_view.py").read_text())


if __name__=="__main__":
    unittest.main()
