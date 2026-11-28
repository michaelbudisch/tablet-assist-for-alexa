"""Regression tests for the LAN-only worker voice-management proxy."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import voice_manager


class VoiceManagerTests(unittest.TestCase):
    def test_unconfigured_worker_rejected(self):
        with patch("voice_manager.load_supervisor_options", return_value={"gpu_base": ""}):
            with self.assertRaises(voice_manager.VoiceManagerError):
                voice_manager._base("token")

    def test_public_worker_rejected(self):
        with patch("voice_manager.load_supervisor_options",
                   return_value={"gpu_base": "http://example.com:10502"}):
            with self.assertRaises(voice_manager.VoiceManagerError):
                voice_manager._base("token")

    def test_only_digits_one_to_nine_can_be_prepared(self):
        for value in ("../etc/passwd", "default", "10", "", None):
            with self.subTest(value=value):
                with self.assertRaises(voice_manager.VoiceManagerError):
                    voice_manager.prepare("token", value)

    def test_catalog_sanitizes_remote_values(self):
        payload = (b'{"available":true,"mode":"fixed","default_variant":"1",'
                   b'"variants":[{"id":"2","name_de":"Tief","ready":true},'
                   b'{"id":"10","ready":true}],"job":{"state":"idle"}}')
        with patch("voice_manager._request", return_value=(payload, {}, 200)), \
             patch("voice_manager.load_supervisor_options", return_value={"voice_variant": "2"}):
            result = voice_manager.catalog("token")
        self.assertEqual(len(result["variants"]), 9)
        self.assertTrue(result["variants"][1]["ready"])
        self.assertFalse(result["variants"][2]["ready"])
        self.assertEqual(result["selected"], "2")

    def test_preview_refuses_unprepared_voice(self):
        with patch("voice_manager.catalog", return_value={
            "available": True, "variants": [{"id": "2", "ready": False}]}):
            with self.assertRaises(voice_manager.VoiceManagerError):
                voice_manager.preview("token", "2")


if __name__ == "__main__":
    unittest.main()
