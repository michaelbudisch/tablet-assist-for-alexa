"""Strict JSON import, device identity and non-destructive upgrade contracts."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import import_manifest as imp

ID="9b146dd0-6390-4eb9-a676-63fc1fda30ab"


def gpu(host="192.168.178.115"):
    return {
        "schema": "tafa-connection-v1", "kind": "gpu_worker",
        "device_id": ID, "host": host,
        "services": {
            "wyoming_stt": {"enabled":True,"host":host,"port":10300},
            "qwen_tts": {"enabled":True,"url":f"http://{host}:10502"},
            "ollama": {"enabled":True,"url":f"http://{host}:11434","model":"qwen3:4b-instruct"},
        },
    }


def speech(host="192.168.178.120"):
    return {
        "schema": "tafa-connection-v1", "kind": "speech_server",
        "device_id": "fd606e72-1f60-41d3-9b37-6bdc4609360b", "host": host,
        "services": {
            "wyoming_stt": {"enabled":True,"host":host,"port":10300},
            "piper": {"enabled":True,"url":f"http://{host}:5000"},
            "mp3": {"enabled":True,"url":f"http://{host}:5001"},
            "https_audio": {"enabled":False,"url":""},
        },
    }


class ImportTests(unittest.TestCase):
    def test_gpu_manifest_maps_only_owned_options(self):
        value=imp.validate(json.dumps(gpu()))
        changes=imp.proposed_options(value,{"gpu_base":"http://192.168.1.8:10502"})
        self.assertEqual(changes["gpu_stt_host"],"192.168.178.115")
        self.assertEqual(changes["gpu_base"],"http://192.168.178.115:10502")
        self.assertEqual(changes["hardware_profile"],"automatic")
        self.assertNotIn("llm_agent",changes)
        self.assertNotIn("cpu_stt",changes)

    def test_ct_import_safely_sets_piper_fallback_and_mp3(self):
        value=imp.validate(json.dumps(speech()))
        changes=imp.proposed_options(value,{"speech_mode":"local"})
        self.assertEqual(changes["speech_mode"],"external")
        self.assertEqual(changes["external_piper_base"],"http://192.168.178.120:5000")
        self.assertEqual(changes["mp3_base"],"http://192.168.178.120:5001")
        self.assertNotIn("public_audio_base",changes)

    def test_reject_unknown_fields_remote_hosts_and_credentials(self):
        valid=gpu()
        for item in [
            {**valid,"host":"8.8.8.8"},
            {**valid,"host":"127.0.0.1"},
            {**valid,"services":{**valid["services"],"extra":{}}},
            {**valid,"services":{**valid["services"],"qwen_tts":{"enabled":True,"url":"http://192.168.178.115:10501"}}},
            {**valid,"services":{**valid["services"],"ollama":{"enabled":True,"url":"http://192.168.178.115:11434","model":"a;rm -rf"}}},
            {**valid,"services":{**valid["services"],"wyoming_stt":{"host":"192.168.1.2","port":10300,"enabled":True}}},
            {**valid,"services":{**valid["services"],"qwen_tts":{"enabled":"true","url":"http://192.168.178.115:10502"}}},
            {**valid,"api_key":"secret"},
        ]:
            with self.subTest(item=item),self.assertRaises(ValueError):
                imp.validate(json.dumps(item))
        with self.assertRaises(ValueError):
            imp.validate('{"schema":"tafa-connection-v1","schema":"duplicate"}')
        with self.assertRaises(ValueError):
            imp.validate("{}"*7000)

    def test_device_mapping_survives_ip_update(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"records.json"
            first=imp.validate(json.dumps(gpu()))
            imp.save_record(first,{"wyoming_stt":"existing_wyo","ollama":"existing_ollama"},path)
            updated=imp.validate(json.dumps(gpu("192.168.178.116")))
            imp.save_record(updated,{"wyoming_stt":"existing_wyo"},path)
            record=imp.load_records(path)[ID]
            self.assertEqual(record["host"],"192.168.178.116")
            self.assertEqual(record["entries"]["ollama"],"existing_ollama")
            self.assertEqual(record["entries"]["wyoming_stt"],"existing_wyo")
            self.assertEqual(path.stat().st_mode&0o777,0o600)

    def test_preview_needs_confirmation_and_expires(self):
        with patch.object(imp,"RECORD",Path("/this/never-exists")):
            ticket,manifest,changes,prior=imp.preview(json.dumps(gpu()),{})
        self.assertIsNone(prior)
        self.assertTrue(ticket)
        self.assertEqual(imp.consume(ticket)["device_id"],ID)
        with self.assertRaises(ValueError):
            imp.consume(ticket)
        with self.assertRaises(ValueError):
            imp.consume("invalid")
        panel=imp.render_panel("de","csrf-token",review=(ticket,manifest,changes,None))
        self.assertIn('name="action" value="manifest_preview"',panel)
        self.assertIn('name="action" value="manifest_apply"',panel)
        self.assertIn('name="ticket"',panel)
        self.assertIn('type="file"',panel)


if __name__=="__main__":
    unittest.main()
