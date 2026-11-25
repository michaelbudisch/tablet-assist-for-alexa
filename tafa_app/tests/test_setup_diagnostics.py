"""App-first setup, read-only service diagnostics and restricted cache deletion."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import model_store
import speech_source
import auto_setup


class Tests(unittest.TestCase):
    def with_options(self, values):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        optionfile=Path(tmp.name)/"options.json"
        optionfile.write_text(json.dumps(values),encoding="utf-8")
        return optionfile

    def test_first_run_setup_fields(self):
        path=self.with_options({
            "speech_mode":"external",
            "external_piper_base":"http://192.168.1.50:5000",
            "gpu_base":"http://192.168.1.60:10502",
            "hardware_profile":"automatic",
            "voice_variant":"2",
            "live_profile":"studio",
            "mp3_base":"http://192.168.1.50:5001",
            "public_audio_base":"https://example.org",
            "mp3_profile":"announcement",
            "chime":True,
        })
        opts=speech_source.setup_settings(path)
        self.assertEqual(opts["gpu_base"],"http://192.168.1.60:10502")
        self.assertEqual(opts["mp3_base"],"http://192.168.1.50:5001")
        self.assertEqual(opts["voice_variant"],"2")
        self.assertTrue(opts["chime"])
        self.assertEqual(speech_source.choose(path)[0],"external")

    def test_never_probe_public_gpu_or_mp3(self):
        for url in ("http://8.8.8.8:10502", "http://127.0.0.1:10502",
                    "https://192.168.1.3:10502", "http://example.com:10502",
                    "http://private.local:10502/status", "http://user:pass@192.168.1.3:10502"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    speech_source.setup_settings(self.with_options({"gpu_base":url}))

    def test_read_only_qwen_route_and_fallback(self):
        opts={"gpu_base":"http://192.168.1.60:10502",
              "mp3_base":"http://192.168.1.50:5001",
              "hardware_profile":"automatic"}
        with patch.object(speech_source,"read_health",side_effect=[
            {"ready":True,"busy":False,"worker_version":"2.2.1"},
            {"status":"online"}]):
            result=speech_source.connection_status(opts,True)
        self.assertEqual((result["route"],result["gpu"],result["mp3"]),("qwen","ready","ready"))
        with patch.object(speech_source,"read_health",side_effect=[None,None]):
            fallback=speech_source.connection_status(opts,True)
        self.assertEqual(fallback["route"],"piper")
        self.assertEqual(fallback["gpu"],"offline")
        with patch.object(speech_source,"read_health",side_effect=[None,None]):
            unavailable=speech_source.connection_status(opts,False)
        self.assertEqual(unavailable["route"],"none")

    def test_mode_cpu_uses_piper_even_with_gpu(self):
        with patch.object(speech_source,"read_health",return_value={"ready":True}):
            result=speech_source.connection_status(
                {"gpu_base":"http://192.168.1.60:10502",
                 "mp3_base":"","hardware_profile":"cpu"}, True)
        self.assertEqual(result["route"],"piper")

    def test_cleanup_only_own_models_in_external_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"tafa_speech"
            voices=root/"voices"
            models=root/"models"
            voices.mkdir(parents=True)
            models.mkdir()
            (voices/model_store.VOICE).write_bytes(b"a"*100)
            (voices/(model_store.VOICE+".json")).write_bytes(b"b"*20)
            (voices/"another-voice.onnx").write_bytes(b"must remain")
            (models/"cache.bin").write_bytes(b"c"*50)
            outside=Path(tmp)/"other-addon.bin"
            outside.write_bytes(b"must remain")
            with patch.object(model_store,"ROOT",root):
                self.assertEqual(model_store.inventory(),
                                 {"piper_bytes":120,"whisper_bytes":50})
                with self.assertRaises(ValueError):
                    model_store.remove_local_models("local")
                self.assertEqual(model_store.remove_local_models("external"),
                                 {"piper_bytes":120,"whisper_bytes":50})
                self.assertEqual(model_store.inventory(),
                                 {"piper_bytes":0,"whisper_bytes":0})
                self.assertTrue((voices/"another-voice.onnx").exists())
                self.assertEqual(outside.read_bytes(),b"must remain")

    def test_symlink_cache_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"tafa_speech"
            root.mkdir()
            outside=Path(tmp)/"outside"
            outside.mkdir()
            (outside/"data.bin").write_bytes(b"safe")
            (root/"models").symlink_to(outside,target_is_directory=True)
            with patch.object(model_store,"ROOT",root):
                with self.assertRaises(ValueError):
                    model_store.remove_local_models("external")
            self.assertTrue((outside/"data.bin").exists())

    def test_initial_entry_prefilled_without_extra_tokens(self):
        calls=[]
        def request(path,data=None,method="POST"):
            calls.append((path,data,method))
            if path=="config/config_entries/flow":
                return {"type":"form","flow_id":"new-flow"}
            if method=="DELETE":
                return {}
            if path.endswith("/new-flow"):
                return {"type":"create_entry"}
            raise AssertionError(path)
        with patch.object(auto_setup,"TOKEN","core-token"), \
             patch.object(auto_setup,"call",side_effect=request):
            result=auto_setup.configure("http://192.168.1.50:5000",
                {"gpu_base":"http://192.168.1.60:10502",
                 "voice_variant":"2","mp3_base":"http://192.168.1.50:5001"})
        self.assertEqual(result,"configured")
        fields=calls[1][1]
        self.assertEqual(fields["gpu_base"],"http://192.168.1.60:10502")
        self.assertEqual(fields["voice_variant"],"2")
        self.assertFalse(any("token" in key.lower() for key in fields))


if __name__ == "__main__":
    unittest.main()
