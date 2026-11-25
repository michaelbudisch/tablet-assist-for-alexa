"""Mock HA Supervisor APIs to test TAFA automatic configuration and pipeline creation."""
import json
import sys
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auto_setup

def fake_connect(responses,on_sent):
    class WS:
        def __init__(self):
            self.replies=deque([{"type":"auth_required"}])
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def send(self,wire):
            msg=json.loads(wire)
            on_sent.append(msg)
            if msg.get("type")=="auth":
                self.replies.append({"type":"auth_ok"})
                return
            kind=msg["type"]
            if kind=="config/entity_registry/list":
                value=[
                    dict(entity_id="stt.tafa",platform="tablet_assist_for_alexa",unique_id="unit_stt_router",disabled_by=None),
                    dict(entity_id="tts.tafa_piper",platform="tablet_assist_for_alexa",unique_id="unit_piper",disabled_by=None),
                    *([dict(entity_id="tts.tafa_stream",platform="tablet_assist_for_alexa",unique_id="unit_stream",disabled_by=None)] if responses.get("stream",True) else []),
                    dict(entity_id="conversation.tafa",platform="tablet_assist_for_alexa",unique_id="unit_conversation_router",disabled_by=None)
                ] if responses.get("entities",True) else []
                value.extend(
                    dict(entity_id=f"stt.wyoming_{i}",platform="wyoming",
                         unique_id=f"wyoming_stt_{i}",disabled_by=None)
                    for i in range(responses.get("wyoming_count",0))
                )
            elif kind=="assist_pipeline/pipeline/list":
                value={"pipelines":responses.get("pipelines",[])}
            elif kind=="assist_pipeline/pipeline/create":
                value={"id":"tafa"}
            elif kind=="tablet_assist_for_alexa/sync_app_configuration":
                value={"changed":True}
            else:
                raise AssertionError("Unexpected HA request: "+kind)
            self.replies.append({"id":msg["id"],"success":True,"result":value})
        def recv(self,timeout=10):
            return json.dumps(self.replies.popleft())
    return lambda *args,**kwargs:WS()

class Tests(unittest.TestCase):
    def invoke(self,responses, **params):
        sent=[]
        client=types.ModuleType("websockets.sync.client")
        client.connect=fake_connect(responses,sent)
        sync=types.ModuleType("websockets.sync")
        sync.client=client
        root=types.ModuleType("websockets")
        root.sync=sync
        with patch.dict(sys.modules,{"websockets":root,"websockets.sync":sync,"websockets.sync.client":client}):
            with patch.object(auto_setup,"TOKEN","test-only-token"):
                result=auto_setup.ensure_pipeline(**params)
        return result,sent
    def test_creates_pipeline_with_complete_required_schema(self):
        result,sent=self.invoke({})
        self.assertEqual(result,"pipeline_created")
        created=next(msg for msg in sent if msg.get("type")=="assist_pipeline/pipeline/create")
        self.assertEqual(created["name"],"TAFA Lokal")
        self.assertEqual(created["stt_engine"],"stt.tafa")
        self.assertEqual(created["conversation_engine"],"conversation.tafa")
        self.assertEqual(created["tts_engine"],"tts.tafa_stream")
        self.assertIn("wake_word_entity",created)
        self.assertIn("wake_word_id",created)
        self.assertIsNone(created["wake_word_entity"])
        self.assertIsNone(created["tts_voice"])
    def test_does_not_create_piper_only_pipeline_if_router_missing(self):
        result,sent=self.invoke({"stream":False})
        self.assertEqual(result,"waiting_for_entities")
        self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create" for msg in sent))
    def test_sync_existing_entry_through_authenticated_app_command(self):
        sent=[]
        client=types.ModuleType("websockets.sync.client")
        client.connect=fake_connect({},sent)
        sync=types.ModuleType("websockets.sync")
        sync.client=client
        root=types.ModuleType("websockets")
        root.sync=sync
        with patch.dict(sys.modules,{"websockets":root,"websockets.sync":sync,
                                     "websockets.sync.client":client}):
            with patch.object(auto_setup,"TOKEN","supervisor-internal"):
                result=auto_setup.sync_app_configuration(
                    "http://192.168.1.50:5000",
                    {"gpu_base":"http://192.168.1.60:10502","cpu_stt":"stt.whisper",
                     "hardware_profile":"automatic"})
        self.assertEqual(result,"changed")
        message=next(msg for msg in sent if msg.get("type")==
                     "tablet_assist_for_alexa/sync_app_configuration")
        self.assertEqual(message["settings"]["cpu_stt"],"stt.whisper")
        self.assertEqual(message["settings"]["gpu_base"],"http://192.168.1.60:10502")
        self.assertNotIn("api_key",message["settings"])

    def test_existing_pipeline_preserved(self):
        result,sent=self.invoke({"pipelines":[{"name":"TAFA Lokal","id":"existing",
                                                "stt_engine":"stt.existing",
                                                "tts_engine":"tts.existing",
                                                "conversation_engine":"conversation.existing"}]})
        self.assertEqual(result,"pipeline_exists")
        self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create" for msg in sent))
    def test_existing_incomplete_pipeline_is_not_reported_ready_or_overwritten(self):
        result, sent = self.invoke({"pipelines":[{"name":"TAFA Lokal", "id":"existing",
                                                  "stt_engine":"stt.configured",
                                                  "tts_engine":None,
                                                  "conversation_engine":"conversation.configured"}]})
        self.assertEqual(result,"pipeline_needs_review")
        self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create" for msg in sent))

    def test_external_proxmox_waits_for_wyoming_whisper(self):
        for count in (0, 2):
            result, sent = self.invoke({"wyoming_count":count}, external_wyoming=True)
            self.assertEqual(result,"waiting_for_external_stt")
            self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create"
                                 for msg in sent))

    def test_external_proxmox_auto_selects_one_wyoming_provider(self):
        result, sent = self.invoke({"wyoming_count":1}, external_wyoming=True)
        self.assertEqual(result,"pipeline_created")
        self.assertTrue(any(msg.get("type")=="assist_pipeline/pipeline/create"
                            for msg in sent))

    def test_external_proxmox_accepts_explicit_provider_with_many_choices(self):
        result, _ = self.invoke({"wyoming_count":2},
                                external_wyoming=True, configured_stt="stt.wyoming_1")
        self.assertEqual(result,"pipeline_created")
        result, sent = self.invoke({"wyoming_count":1},
                                   external_wyoming=True, configured_stt="stt.missing")
        self.assertEqual(result,"waiting_for_external_stt")
        self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create"
                             for msg in sent))

    def test_wait_for_registered_entities(self):
        result,sent=self.invoke({"entities":False})
        self.assertEqual(result,"waiting_for_entities")
        self.assertFalse(any(msg.get("type")=="assist_pipeline/pipeline/create" for msg in sent))
    def test_config_flow_preserves_ha_managed_setup(self):
        calls=[]
        def request(path,data=None,method="POST"):
            calls.append((path,data,method))
            if path=="config/config_entries/flow":return {"type":"form","flow_id":"safe-flow"}
            if method=="DELETE":return {}
            if path.endswith("safe-flow"):return {"type":"create_entry","result":"ok"}
            raise AssertionError(path)
        with patch.object(auto_setup,"TOKEN","test-only-token"),patch.object(auto_setup,"call",side_effect=request):
            self.assertEqual(auto_setup.configure("http://tafa-internal:5000"),"configured")
        self.assertEqual(calls[1][1]["piper_base"],"http://tafa-internal:5000")
        self.assertTrue(any(method=="DELETE" for _,_,method in calls))
if __name__=="__main__":unittest.main()
