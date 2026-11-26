"""Safe and reproducible Voice Test contracts; no microphone or live HA required."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import json

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import voice_test
from voice_test_view import render_voice_panel, public_device_snapshot


class FakeWS:
    def __init__(self, messages):
        self.messages = [dict(x) for x in messages]
        self.sent = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def send(self, message):
        self.sent.append(message)
    def recv(self, timeout=None):
        if not self.messages:
            raise AssertionError("Unexpected WebSocket recv")
        return json.dumps(self.messages.pop(0))


def msg(kind, data=None):
    return {"id": 10, "type": "event", "event": {"type": kind, "data": data or {}}}


class VoiceTestContracts(unittest.TestCase):
    def pipeline(self):
        return {"id":1,"type":"result","success":True,"result":{
            "pipelines":[{"id":"tafa-1","name":"TAFA Lokal","stt_engine":"stt.tafa"}]}}

    def test_speech_runs_existing_pipeline_and_streams_pcm(self):
        replies = [
            self.pipeline(),
            {"id":10,"type":"result","success":True,"result":None},
            msg("run-start",{"runner_data":{"stt_binary_handler_id":17}}),
            msg("stt-start"), msg("stt-end",{"stt_output":{"text":"Wie ist das Wetter?"}}),
            msg("intent-start"), msg("intent-end",{"intent_output":{
                "response":{"speech":{"plain":{"speech":"Heute ist es wolkig."}}},
                "conversation_id":"safe-id"}}),
            msg("tts-start"),msg("tts-end",{"tts_output":{"url":"/api/tts_proxy/abc.wav"}}),
            msg("run-end")]
        socket=FakeWS(replies)
        with patch.object(voice_test,"_open_ws",return_value=socket):
            result=voice_test.run_voice("test-only-token",pcm=b"\x00\x01"*16000)
        self.assertEqual(result["transcript"],"Wie ist das Wetter?")
        self.assertEqual(result["reply"],"Heute ist es wolkig.")
        self.assertEqual(result["conversation_id"],"safe-id")
        self.assertTrue(result["audio_id"])
        commands=[json.loads(x) for x in socket.sent if isinstance(x,str)]
        self.assertEqual(commands[1]["type"],"assist_pipeline/run")
        self.assertEqual(commands[1]["pipeline"],"tafa-1")
        self.assertEqual(commands[1]["start_stage"],"stt")
        self.assertEqual(commands[1]["end_stage"],"tts")
        binary=[x for x in socket.sent if isinstance(x,bytes)]
        self.assertTrue(binary)
        self.assertTrue(all(x[0]==17 for x in binary))
        self.assertEqual(binary[-1],b"\x11")
        self.assertIsNotNone(result["timings"]["stt_ms"])

    def test_read_only_status_reports_only_actual_entity_attributes(self):
        registry=[
            {"entity_id":"stt.tafa","platform":"tablet_assist_for_alexa","unique_id":"my_stt_router"},
            {"entity_id":"tts.tafa","platform":"tablet_assist_for_alexa","unique_id":"my_stream"},
            {"entity_id":"conversation.tafa","platform":"tablet_assist_for_alexa","unique_id":"my_conversation_router"},
        ]
        states=[
            {"entity_id":"stt.tafa","state":"unknown","attributes":{"letztes_backend":"homeserver","letzte_dauer_ms":1250}},
            {"entity_id":"tts.tafa","state":"unknown","attributes":{"letztes_backend":"Piper","erste_audio_ms":800}},
        ]
        socket=FakeWS([self.pipeline(),{"id":2,"type":"result","success":True,"result":registry},
                       {"id":3,"type":"result","success":True,"result":states}])
        with patch.object(voice_test,"_open_ws",return_value=socket):
            output=voice_test.voice_status("test-only-token")
        self.assertEqual(output["pipeline"],"TAFA Lokal")
        self.assertEqual(output["entities"]["stt"]["backend"],"homeserver")
        self.assertEqual(output["entities"]["stt"]["duration_ms"],1250)
        self.assertEqual(output["entities"]["tts"]["first_audio_ms"],800)

    def test_reject_unexpected_content_and_remote_audio(self):
        with self.assertRaises(voice_test.VoiceTestError):
            voice_test.run_voice("ignored",pcm=b"bad")
        with self.assertRaises(voice_test.VoiceTestError):
            voice_test.run_voice("ignored",text="x"*301)
        with self.assertRaises(voice_test.VoiceTestError):
            voice_test.run_voice("ignored",text="hello",conversation_id="../../settings")
        self.assertEqual(voice_test._tts_path("https://evil.example/other/path"),"")
        self.assertEqual(voice_test._tts_path("/api/tts_proxy/abc.wav?url=evil"),"")
        self.assertEqual(voice_test._tts_path("/api/tts_proxy/abc.wav"),"/api/tts_proxy/abc.wav")

    def test_voice_ui_escapes_devices_and_controls_native_device_only(self):
        state={"devices":[{"device_id":"a"*32,"room":"<bad>","online":True,"muted":True,
             "telemetry":{"microphone":"muted","bluetooth":"connected","secret":"never"}}],
             "users":[{"id":"secret-user"}]}
        markup=render_voice_panel("de","token",state)
        self.assertIn('data-native-mode="wake"',markup)
        self.assertIn('data-native-mode="mute"',markup)
        self.assertIn('data-native-mode="continuous"',markup)
        self.assertIn('aria-pressed="false" disabled',markup)
        self.assertIn("&lt;bad&gt;",markup)
        self.assertNotIn("<bad>",markup)
        self.assertIn("Android-App",markup)
        self.assertIn("Einmal sprechen",markup)
        self.assertNotIn("<script",markup)
        public=public_device_snapshot(state)
        self.assertEqual(len(public["devices"]),1)
        self.assertNotIn("users",public)
        self.assertNotIn("secret",public["devices"][0]["telemetry"])
        self.assertEqual(public["devices"][0]["telemetry"]["bluetooth"],"connected")

    def test_no_browser_wakeword_loop_and_csrf_native_controls(self):
        js=(APP/"voice-test.js").read_text()
        server=(APP/"server.py").read_text()
        self.assertNotIn("kind=wake",js)
        self.assertNotIn("runLoop(",js)
        self.assertNotIn("chooseMode(",js)
        self.assertIn('postForm("voice_device_mode"',js)
        self.assertIn('postForm("voice_devices"',js)
        self.assertIn('["mute","wake"]',js)
        self.assertIn('update_device({"device_id":[identifier],"setting":["muted"]',server)
        self.assertIn('target not in ("mute","wake")',server)
        self.assertIn('kind[0] != "turn"',server)
        self.assertNotIn('run_voice(TOKEN,pcm=payload,wake=',server)


if __name__ == "__main__":
    unittest.main()
