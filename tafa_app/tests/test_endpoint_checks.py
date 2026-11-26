"""Private-only, read-only diagnostics for the unified TAFA settings UI."""
import json
import sys
import types
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import endpoint_checks as checks
import settings_ui


class SocketContext:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class EndpointTests(unittest.TestCase):
    def test_host_suggested_only_for_private_lan_qwen_url(self):
        self.assertEqual(checks.suggested_gpu_stt_host("http://192.168.178.115:10502"),
                         "192.168.178.115")
        for url in ("", "https://192.168.1.4:10502",
                    "http://8.8.8.8:10502", "http://outside.example.com:10502",
                    "http://user:pass@192.168.1.4:10502"):
            with self.subTest(url=url):
                self.assertEqual(checks.suggested_gpu_stt_host(url), "")

    def test_bounded_private_gpu_whisper_probe(self):
        with patch.object(checks.socket, "create_connection", return_value=SocketContext()) as connector:
            self.assertEqual(checks.probe_gpu_whisper("192.168.178.115"), "reachable")
            connector.assert_called_once_with(("192.168.178.115", 10300), timeout=0.8)
        with patch.object(checks.socket, "create_connection") as connector:
            for host in ("", "8.8.8.8", "example.org", "127.0.0.1",
                         "1.2.3.4:10300", "http://192.168.1.5"):
                self.assertIn(checks.probe_gpu_whisper(host), ("invalid", "missing"))
            connector.assert_not_called()
        with patch.object(checks.socket, "create_connection", side_effect=TimeoutError):
            self.assertEqual(checks.probe_gpu_whisper("192.168.178.115"), "offline")

    def test_status_does_not_claim_gpu_recognition_from_open_tcp(self):
        opts = {"gpu_stt_host": "192.168.178.115", "gpu_stt": "stt.gpu",
                "cpu_stt": "stt.cpu", "llm_agent": "conversation.ollama",
                "public_audio_base": "https://tafa.example.org"}
        with patch.object(checks, "probe_gpu_whisper", return_value="reachable"):
            result=checks.assess_endpoints(
                opts, "external", {"piper_ready": True},
                {"gpu": "ready", "mp3": "offline"},
                [{"id": "stt.gpu"}, {"id": "stt.cpu"}])
        self.assertEqual(result["gpu_stt_host"], "reachable")
        self.assertEqual(result["gpu_stt"], "selected")
        self.assertEqual(result["cpu_stt"], "selected")
        self.assertEqual(result["public_audio_base"], "configured_unchecked")
        self.assertEqual(result["llm_agent"], "configured_unchecked")
        html=settings_ui.render_settings_form(opts,[], "de", "csrf", "",
                        checks=result, latest={"backend":"homeserver","duration_ms":1749})
        self.assertIn("Letzte Spracherkennung: CPU-/Homeserver",html)
        connections=settings_ui.render_connection_form(opts,"de","csrf",checks=result)
        self.assertIn("Wyoming TCP 10300",connections)
        self.assertIn('name="gpu_stt_host"',connections)
        self.assertNotIn("Letzte Spracherkennung: GPU-Whisper",html)

    def test_url_proposal_visible_but_not_persisted_automatically(self):
        opts={"gpu_base":"http://192.168.178.115:10502", "gpu_stt_host":""}
        de=settings_ui.render_connection_form(opts,"de","csrf")
        self.assertIn('name="gpu_stt_host"',de)
        self.assertIn('value="192.168.178.115"',de)
        self.assertNotIn('name="gpu_stt_host"',
                         settings_ui.render_settings_form(opts,[],"de","csrf",""))

    def test_router_last_backend_comes_from_home_assistant_state(self):
        requests=[]
        class Ws:
            def __init__(self):
                self.responses=deque([{"type":"auth_required"}])
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def recv(self,timeout=3):
                return json.dumps(self.responses.popleft())
            def send(self,wire):
                msg=json.loads(wire)
                requests.append(msg["type"])
                if msg["type"]=="auth":
                    self.responses.append({"type":"auth_ok"})
                elif msg["type"]=="config/entity_registry/list":
                    self.responses.append({"id":1,"success":True,"result":[{
                        "entity_id":"stt.tablet_assist_sprachrouter",
                        "unique_id":"demo_stt_router",
                        "platform":"tablet_assist_for_alexa"}]})
                elif msg["type"]=="get_states":
                    self.responses.append({"id":2,"success":True,"result":[{
                        "entity_id":"stt.tablet_assist_sprachrouter",
                        "attributes":{"letztes_backend":"zusatzrechner",
                                      "letzte_dauer_ms":420}}]})
                else:
                    raise AssertionError(msg)
        client=types.ModuleType("websockets.sync.client")
        client.connect=lambda *args,**kwargs: Ws()
        sync=types.ModuleType("websockets.sync")
        sync.client=client
        root=types.ModuleType("websockets")
        root.sync=sync
        with patch.dict(sys.modules,{"websockets":root,"websockets.sync":sync,
                                     "websockets.sync.client":client}):
            result=checks.recent_stt_backend("fake-token")
        self.assertEqual(result,{"backend":"zusatzrechner","duration_ms":420})
        self.assertEqual(requests,["auth","config/entity_registry/list","get_states"])


if __name__ == "__main__":
    unittest.main()
