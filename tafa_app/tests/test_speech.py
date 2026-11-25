"""Unit-level TAFA CPU API checks; no model downloads."""
import io
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
import wave
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import speech_proxy as speech

class Voice:
    def synthesize_wav(self,text,wav):
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(b"\0\0"*160)

class ASR:
    def transcribe(self,audio,**kwargs):
        with wave.open(audio,"rb") as wav:
            assert wav.getframerate()==16000
        return iter([SimpleNamespace(text=" Test erfolgreich ")]),None

class TestSpeech(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=speech.ThreadingHTTPServer(("127.0.0.1",0),speech.Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url="http://127.0.0.1:"+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)
    def setUp(self):
        speech.STATE.voice=Voice();speech.STATE.asr=ASR()
    def call(self,path,body=None,mime=None):
        headers={"Content-Type":mime} if mime else {}
        request=urllib.request.Request(self.url+path,body,headers=headers,
                                       method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(request,timeout=5) as response:
                return response.status,response.read(),response.headers
        except urllib.error.HTTPError as exc:
            return exc.code,exc.read(),exc.headers
    def test_health(self):
        code,data,_=self.call("/health")
        self.assertEqual(code,200)
        self.assertTrue(json.loads(data)["ready"])
    def test_valid_synthesis(self):
        code,data,headers=self.call("/synthesize",json.dumps({"text":"Hallo"}).encode(),"application/json")
        self.assertEqual(code,200);self.assertEqual(headers.get_content_type(),"audio/wav")
        self.assertTrue(data.startswith(b"RIFF"))
    def test_bounded_text_and_unsupported_type(self):
        code,_,_=self.call("/synthesize",json.dumps({"text":"a"*501}).encode(),"application/json")
        self.assertEqual(code,400)
        code,_,_=self.call("/synthesize",b"abc","text/plain")
        self.assertEqual(code,415)
    def test_stt(self):
        buf=io.BytesIO()
        with wave.open(buf,"wb") as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
            wav.writeframes(b"\0\0"*1000)
        code,data,_=self.call("/stt",buf.getvalue(),"audio/wav")
        self.assertEqual(code,200);self.assertEqual(json.loads(data)["text"],"Test erfolgreich")
    def test_invalid_audio(self):
        code,_,_=self.call("/stt",b"not a wav","audio/wav")
        self.assertEqual(code,400)
    def test_status_includes_model_phases(self):
        speech.STATE.tts_phase="error"
        speech.STATE.stt_phase="error"
        speech.STATE.tts_error="RuntimeError: example model error"
        speech.STATE.stt_error="ImportError: example library error"
        code,data,_=self.call("/status")
        self.assertEqual(code,200)
        payload=json.loads(data)
        self.assertEqual(payload["piper_phase"],"error")
        self.assertIn("ImportError",payload["whisper_error"])
    def test_retry(self):
        speech.STATE.voice=None
        speech.STATE.asr=None
        speech.STATE.tts_phase="error"
        speech.STATE.stt_phase="error"
        from unittest.mock import patch
        with patch.object(speech.STATE,"retry",return_value=True) as retry:
            code,data,_=self.call("/retry",b"{}","application/json")
        self.assertEqual(code,200)
        self.assertTrue(json.loads(data)["accepted"])
        retry.assert_called_once_with()
    def test_busy(self):
        speech.STATE.stt_lock.acquire()
        try:
            code,_,_=self.call("/stt",b"RIFF" + b"\0"*100,"audio/wav")
            self.assertEqual(code,429)
        finally:
            speech.STATE.stt_lock.release()
if __name__=="__main__":
    unittest.main()
