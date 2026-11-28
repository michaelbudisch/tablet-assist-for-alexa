"""Exercise the real TAFA import POST with stale and racing Wyoming options.

This closes the gap between pure reconciliation tests and the actual
Control Center handler, including its final Supervisor options read.
No Home Assistant server, worker, credentials or network requests required.
"""
from email.message import Message
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import server
import settings_ui
from import_manifest import validate


WORKER_ID="9b146dd0-6390-4eb9-a676-63fc1fda30ab"


def worker():
    host="192.168.178.115"
    return validate(json.dumps({
        "schema":"tafa-connection-v1",
        "kind":"gpu_worker",
        "device_id":WORKER_ID,
        "host":host,
        "services":{
            "wyoming_stt":{"host":host,"port":10300,"enabled":True},
            "qwen_tts":{"url":f"http://{host}:10502","enabled":True},
            "ollama":{"url":f"http://{host}:11434","enabled":False,"model":""},
        }
    }))


def run_import(current,latest):
    submitted=urlencode({
        "csrf":"test-csrf","lang":"de","tab":"setup",
        "action":"manifest_apply","ticket":"approved",
    }).encode("utf-8")
    handler=object.__new__(server.Handler)
    handler.path="/"
    handler.allowed=lambda: True
    handler.rfile=io.BytesIO(submitted)
    handler.headers=Message()
    handler.headers["Content-Length"]=str(len(submitted))
    handler.headers["Content-Type"]="application/x-www-form-urlencoded"
    replies=[]
    handler.respond=lambda body,status_code=200: replies.append((status_code,body))
    handler.send_error=lambda *args: (_ for _ in ()).throw(
        AssertionError(f"Unexpected HTTP error: {args}"))

    saved=MagicMock()
    saved.status=200
    saved.read.return_value=b'{"result":"ok"}'
    saved.__enter__.return_value=saved
    with patch.object(server,"CSRF","test-csrf"),\
         patch.object(server,"TOKEN","test-supervisor-token"),\
         patch.object(server,"consume_import",return_value=worker()),\
         patch.object(server,"load_options",return_value=current),\
         patch.object(settings_ui,"load_options",return_value=latest),\
         patch.object(server,"load_records",return_value={}),\
         patch.object(server,"configure",return_value="already_configured") as configure,\
         patch.object(server,"provision_worker_manifest",return_value={
             "entries":{"wyoming_stt":"new-wyoming-entry"},
             "entities":{"stt":"stt.gpu_whisper"},"messages":[]}),\
         patch.object(server,"save_record") as record,\
         patch.object(server,"activate_configured_services"),\
         patch.object(server,"display",return_value="done"),\
         patch.object(settings_ui.urllib.request,"urlopen",return_value=saved) as urlopen:
        handler.do_POST()

    if urlopen.call_count:
        stored=json.loads(urlopen.call_args.args[0].data)["options"]
    else:
        stored=None
    return replies,stored,configure,record


class ImportPostTests(unittest.TestCase):
    def test_reimport_fixes_preexisting_duplicate_before_ha_setup(self):
        old={"speech_mode":"local",
             "cpu_stt":"stt.gpu_whisper","gpu_stt":"stt.gpu_whisper"}
        response,stored,configured,record=run_import(old,old)
        self.assertEqual(response,[(200,"done")])
        self.assertEqual(stored["cpu_stt"],"")
        self.assertEqual(stored["gpu_stt"],"stt.gpu_whisper")
        self.assertEqual(configured.call_count,1)
        settings=configured.call_args.args[1]
        self.assertEqual(settings["cpu_stt"],"")
        self.assertEqual(settings["gpu_stt"],"stt.gpu_whisper")
        record.assert_called_once()

    def test_reimport_handles_new_duplicate_at_final_supervisor_save(self):
        before={"speech_mode":"local","cpu_stt":"stt.gpu_whisper","gpu_stt":""}
        latest={**before,"gpu_stt":"stt.gpu_whisper"}
        response,stored,configured,record=run_import(before,latest)
        self.assertEqual(response,[(200,"done")])
        self.assertEqual(stored["cpu_stt"],"")
        self.assertEqual(stored["gpu_stt"],"stt.gpu_whisper")
        record.assert_called_once()

    def test_reimport_does_not_clear_distinct_real_cpu(self):
        old={"speech_mode":"external","external_piper_base":"http://192.168.178.120:5000",
             "cpu_stt":"stt.proxmox","gpu_stt":"stt.old_gpu"}
        response,stored,configured,record=run_import(old,old)
        self.assertEqual(response,[(200,"done")])
        self.assertEqual(stored["cpu_stt"],"stt.proxmox")
        self.assertEqual(stored["gpu_stt"],"stt.gpu_whisper")
        record.assert_called_once()


if __name__=="__main__":
    unittest.main()
