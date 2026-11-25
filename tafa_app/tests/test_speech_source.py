"""External Proxmox speech is explicit, LAN-only and never starts bundled models."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
from speech_source import choose


class SpeechSourceTests(unittest.TestCase):
    def selection(self, settings):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "options.json"
            p.write_text(json.dumps(settings), encoding="utf-8")
            return choose(p)

    def test_setup_mode_is_not_local_model_mode(self):
        self.assertEqual(self.selection({"speech_mode":"setup"}),("setup",""))

    def test_default_and_explicit_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(choose(Path(tmp) / "missing.json"), ("local", ""))
        self.assertEqual(self.selection({"speech_mode": "local"}), ("local", ""))

    def test_private_proxmox_url(self):
        self.assertEqual(
            self.selection({"speech_mode": "external",
                            "external_piper_base": "http://192.168.178.60:5000/"}),
            ("external", "http://192.168.178.60:5000"))
        self.assertEqual(
            self.selection({"speech_mode": "external",
                            "external_piper_base": "http://speechserver.local:5000"}),
            ("external", "http://speechserver.local:5000"))

    def test_invalid_urls_fail_closed(self):
        for base in ("", "http://127.0.0.1:5000", "http://8.8.8.8:5000",
                     "http://evil.example:5000", "https://192.168.178.60:5000",
                     "http://192.168.178.60:5000/path",
                     "http://name:pass@192.168.178.60:5000"):
            with self.subTest(base=base):
                with self.assertRaises(ValueError):
                    self.selection({"speech_mode": "external",
                                    "external_piper_base": base})

    def test_external_startup_skips_local_worker(self):
        with patch.object(server, "bootstrap", return_value=[]), \
             patch.object(server, "choose_speech_source",
                          return_value=("external", "http://192.168.178.60:5000")), \
             patch.object(server, "monitor_speech") as monitor, \
             patch.object(server, "publish_service_address") as publish, \
             patch.object(server.threading, "Thread") as thread:
            server.startup()
        monitor.assert_not_called()
        publish.assert_called_once_with("http://192.168.178.60:5000")
        self.assertEqual(thread.call_count, 1)
        self.assertEqual(thread.call_args.kwargs["args"],
                         ("http://192.168.178.60:5000", "external"))

    def test_external_ready_requires_wyoming_before_pipeline(self):
        states = []
        with patch.object(server, "external_piper_ready", return_value=True), \
             patch.object(server, "configure", return_value="configured"), \
             patch.object(server, "sync_app_configuration", return_value="changed") as sync, \
             patch.object(server, "ensure_pipeline", return_value="pipeline_exists") as pipeline, \
             patch.object(server, "save_state", side_effect=lambda *args: states.append(args)):
            server.autoconfigure("http://192.168.178.60:5000", "external")
        pipeline.assert_called_once_with(external_wyoming=True, configured_stt="")
        sync.assert_called_once()
        self.assertEqual(states[-1][0], "external_ready")


    def test_external_wyoming_pending_preserves_tts_and_pairing_setup(self):
        states = []
        with patch.object(server, "external_piper_ready", return_value=True), \
             patch.object(server, "configure", return_value="configured") as configure, \
             patch.object(server, "sync_app_configuration", return_value="changed") as sync, \
             patch.object(server, "ensure_pipeline", return_value="waiting_for_external_stt") as pipeline, \
             patch.object(server, "save_state", side_effect=lambda *args: states.append(args)), \
             patch.object(server.time, "sleep", side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                server.autoconfigure("http://192.168.178.60:5000", "external")
        configure.assert_called_once()
        sync.assert_called_once()
        pipeline.assert_called_once_with(external_wyoming=True, configured_stt="")
        self.assertEqual(states[-1][0], "waiting_for_external_stt")



if __name__ == "__main__":
    unittest.main()
