"""JSON reimport compatibility with an old, still-loaded HA integration.

The modern backend directly recreates a deleted Wyoming entry. Older HA Core
processes may still have the previous strict handler loaded until Core restarts.
TAFA must recover only the specific stale-mapping error, not swallow real errors.
"""
import json
import sys
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import auto_setup

MISSING={"id":0,"success":False,
         "error":{"code":"provision_failed",
                  "message":"Previously mapped integration missing; review first"}}
SUCCESS={"id":0,"success":True,
         "result":{"entries":{"wyoming_stt":"new-wyoming-id"},
                   "entities":{"stt":"stt.new_whisper"},"messages":[]}}
UNREACHABLE={"id":0,"success":False,
             "error":{"code":"provision_failed",
                      "message":"wyoming flow did not finish: {'base': 'cannot_connect'}"}}


def simulate(outcomes,tracked,enabled=None):
    if enabled is None:
        enabled={"wyoming_stt":True,"ollama":False}
    calls=[]
    manifest={"kind":"gpu_worker","host":"10.0.0.13","device_id":"a-uuid-for-test",
              "services":{k:{"enabled":v} for k,v in enabled.items()}}

    class Connection:
        def __init__(self):
            self.replies=deque([{"type":"auth_required"}])
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def send(self,wire):
            request=json.loads(wire)
            if request.get("type")=="auth":
                self.replies.append({"type":"auth_ok"})
                return
            calls.append(request)
            index=len(calls)-1
            if index>=len(outcomes):
                raise AssertionError("Unexpected extra HA configuration attempt")
            reply={**outcomes[index],"id":request["id"]}
            self.replies.append(reply)
        def recv(self,timeout=10):
            return json.dumps(self.replies.popleft())

    client=types.ModuleType("websockets.sync.client")
    client.connect=lambda *args,**kwargs:Connection()
    sync=types.ModuleType("websockets.sync")
    sync.client=client
    websocket=types.ModuleType("websockets")
    websocket.sync=sync
    with patch.dict(sys.modules,{"websockets":websocket,
                                 "websockets.sync":sync,
                                 "websockets.sync.client":client}),\
         patch.object(auto_setup,"TOKEN","test-supervisor-token"):
        try:
            return auto_setup.provision_worker_manifest(manifest,tracked),calls
        except RuntimeError as exc:
            return exc,calls


class CompatibilityTests(unittest.TestCase):
    def test_old_wyoming_entry_deleted_retry_recreates_it(self):
        outcome,calls=simulate([MISSING,SUCCESS],{"wyoming_stt":"old-id"})
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[0]["tracked"],{"wyoming_stt":"old-id"})
        self.assertEqual(calls[1]["tracked"],{})
        self.assertEqual(calls[1]["manifest"],calls[0]["manifest"])
        self.assertEqual(outcome["entries"]["wyoming_stt"],"new-wyoming-id")
        self.assertIn("repariert",outcome["messages"][0])

    def test_missing_ollama_does_not_drop_present_wyoming_before_exhausting(self):
        result,calls=simulate([MISSING,MISSING,SUCCESS],
            {"wyoming_stt":"known-stt","ollama":"deleted-ollama"},
            {"wyoming_stt":True,"ollama":True})
        self.assertEqual(len(calls),3)
        self.assertEqual(calls[0]["tracked"],
                         {"wyoming_stt":"known-stt","ollama":"deleted-ollama"})
        self.assertEqual(calls[1]["tracked"],{"ollama":"deleted-ollama"})
        self.assertEqual(calls[2]["tracked"],{})
        self.assertEqual(result["entities"]["stt"],"stt.new_whisper")

    def test_other_provisioning_errors_are_not_retried(self):
        result,calls=simulate([UNREACHABLE],{"wyoming_stt":"old-id"})
        self.assertIsInstance(result,RuntimeError)
        self.assertIn("cannot_connect",str(result))
        self.assertEqual(len(calls),1)

    def test_modern_backend_has_no_extra_attempts(self):
        result,calls=simulate([SUCCESS],{"wyoming_stt":"valid-id"})
        self.assertEqual(len(calls),1)
        self.assertEqual(result["entries"]["wyoming_stt"],"new-wyoming-id")
        self.assertEqual(result["messages"],[])

    def test_no_unnecessary_retries_when_unmapped(self):
        result,calls=simulate([MISSING],{})
        self.assertIsInstance(result,RuntimeError)
        self.assertEqual(len(calls),1)


if __name__=="__main__":
    unittest.main()
