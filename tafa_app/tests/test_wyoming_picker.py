"""Wyoming entity picker: truthful discovery, no guessing, safe option writes."""
import io
import json
import sys
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import wyoming_picker
import server


def connection(entries,requests):
    class WS:
        def __init__(self):self.responses=deque([{"type":"auth_required"}])
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def recv(self,timeout=8):return json.dumps(self.responses.popleft())
        def send(self,wire):
            msg=json.loads(wire)
            requests.append(msg)
            if msg["type"]=="auth":self.responses.append({"type":"auth_ok"})
            elif msg["type"]=="config/entity_registry/list":
                self.responses.append({"id":msg["id"],"success":True,"result":entries})
            else:raise AssertionError(msg)
    return lambda *args,**kwargs:WS()


class PickerTests(unittest.TestCase):
    def lookup(self,entries,token="fake-supervisor-token"):
        requests=[]
        client=types.ModuleType("websockets.sync.client")
        client.connect=connection(entries,requests)
        sync=types.ModuleType("websockets.sync");sync.client=client
        root=types.ModuleType("websockets");root.sync=sync
        with patch.dict(sys.modules,{"websockets":root,"websockets.sync":sync,
                                    "websockets.sync.client":client}):
            rows=wyoming_picker.discover_wyoming_stt(token)
        return rows,requests

    def test_wyoming_stt_only_and_sorted(self):
        rows,wire=self.lookup([
            {"entity_id":"stt.gpu_whisper","platform":"wyoming","name":"GPU Whisper","disabled_by":None},
            {"entity_id":"stt.cpu_whisper","platform":"wyoming","name":"CPU Whisper","disabled_by":None},
            {"entity_id":"stt.disabled","platform":"wyoming","disabled_by":"user"},
            {"entity_id":"stt.other","platform":"other","disabled_by":None},
            {"entity_id":"tts.whisper","platform":"wyoming","disabled_by":None}
        ])
        self.assertEqual([r["id"] for r in rows],["stt.cpu_whisper","stt.gpu_whisper"])
        self.assertEqual(wire[-1]["type"],"config/entity_registry/list")

    def test_none_detected_is_safe(self):
        rows,_=self.lookup([])
        self.assertEqual(rows,[])
        with self.assertRaises(ValueError):
            wyoming_picker.validate_selection("stt.cpu","",rows)

    def test_separate_cpu_and_gpu_and_stale_rejected(self):
        rows=[{"id":"stt.cpu"},{"id":"stt.gpu"}]
        self.assertEqual(wyoming_picker.validate_selection("stt.cpu","stt.gpu",rows),
                         {"cpu_stt":"stt.cpu","gpu_stt":"stt.gpu"})
        for c,g in (("stt.cpu","stt.cpu"),("stt.not_registered","stt.gpu"),
                    ("", "stt.stale")):
            with self.subTest(cpu=c,gpu=g),self.assertRaises(ValueError):
                wyoming_picker.validate_selection(c,g,rows)

    def test_saves_only_two_fields_with_original_options_preserved(self):
        previous={"gpu_base":"http://192.168.178.115:10502",
                  "llm_agent":"conversation.ollama_conversation",
                  "cpu_stt":"stt.old","gpu_stt":""}
        class Reply:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,n):return b'{"result":"ok"}'
        calls=[]
        def fake_open(req,timeout):
            calls.append((req.full_url,req.get_method(),json.loads(req.data)))
            return Reply()
        with patch.object(wyoming_picker,"load_supervisor_options",return_value=previous),\
             patch.object(wyoming_picker.urllib.request,"urlopen",side_effect=fake_open):
            saved=wyoming_picker.save_wyoming_selection(
                "supervisor-token","stt.cpu","stt.gpu",
                [{"id":"stt.cpu"},{"id":"stt.gpu"}])
        self.assertEqual(saved,{"cpu_stt":"stt.cpu","gpu_stt":"stt.gpu"})
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][1],"POST")
        updated=calls[0][2]["options"]
        self.assertEqual(updated["llm_agent"],previous["llm_agent"])
        self.assertEqual(updated["gpu_base"],previous["gpu_base"])
        self.assertEqual(updated["gpu_stt"],"stt.gpu")

    def test_invalid_selection_does_not_write_options(self):
        with patch.object(wyoming_picker.urllib.request,"urlopen") as url:
            with self.assertRaises(ValueError):
                wyoming_picker.save_wyoming_selection(
                    "token","stt.same","stt.same",[{"id":"stt.same"}])
            url.assert_not_called()

    def test_ingress_picker_is_escaped_and_bilingual(self):
        entries=[{"id":"stt.cpu","name":"CPU & <Whisper>"},
                 {"id":"stt.gpu","name":"GPU"}]
        options={"cpu_stt":"stt.cpu","gpu_stt":"","llm_agent":""}
        def test_display(lang):
            with patch.object(server,"discover_wyoming_stt",return_value=entries),\
                 patch.object(server,"setup_settings",return_value=options),\
                 patch.object(server,"status",return_value={}),\
                 patch.object(server,"setup_status",return_value={"status":"ready"}),\
                 patch.object(server,"choose_speech_source",return_value=("external","http://192.168.1.2:5000")),\
                 patch.object(server,"external_piper_ready",return_value=True),\
                 patch.object(server,"local_model_inventory",return_value={"piper_bytes":0,"whisper_bytes":0}),\
                 patch.object(server,"connection_status",return_value={"gpu":"offline","gpu_version":"","piper":"ready","mp3":"offline","route":"piper"}):
                return server.display(lang=lang,default_tab="connections")
        german=test_display("de")
        english=test_display("en")
        self.assertIn("CPU &amp; &lt;Whisper&gt;",german)
        self.assertIn("CPU-Whisper",german)
        self.assertIn("GPU Whisper",english)
        self.assertIn('value="stt.cpu" selected',german)
        self.assertIn('name="cpu_stt"',english)
        self.assertIn('name="gpu_stt"',english)
        self.assertNotIn('name="gpu_stt"',english.split('id="tafa-settings"')[1].split("</section>")[0])


if __name__=="__main__":
    unittest.main()
