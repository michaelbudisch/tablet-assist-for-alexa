"""TAFA Ingress HTTP tests without Supervisor or model downloads."""
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.http=server.ThreadingHTTPServer(("127.0.0.1",0),server.Handler)
  cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True)
  cls.thread.start()
  cls.origin="http://127.0.0.1:"+str(cls.http.server_port)
 @classmethod
 def tearDownClass(cls):
  cls.http.shutdown();cls.http.server_close();cls.thread.join(timeout=2)
 def get(self,path="/"):
  try:
   with urllib.request.urlopen(self.origin+path,timeout=5) as response:
    return response.status,response.read().decode("utf-8"),response.headers
  except urllib.error.HTTPError as error:
   return error.code,error.read().decode("utf-8"),error.headers
 def post(self,fields):
  body=urllib.parse.urlencode(fields).encode()
  request=urllib.request.Request(self.origin+"/",body,headers={"Content-Type":"application/x-www-form-urlencoded"})
  try:
   with urllib.request.urlopen(request,timeout=5) as response:
    return response.status,response.read().decode("utf-8")
  except urllib.error.HTTPError as error:
   return error.code,error.read().decode("utf-8")
 def test_ui_bilingual_and_security_headers(self):
  with patch.object(server,"status",return_value={"tablet_assist_for_alexa":"installed · 0.4.0"}),\
       patch.object(server,"speech_status",return_value={"piper_ready":True,"whisper_ready":False}),\
       patch.object(server,"setup_status",return_value={"status":"waiting_for_home_assistant"}):
   code,body,headers=self.get()
   self.assertEqual(code,200)
   self.assertIn("TAFA Control Center",body)
   self.assertIn("Piper",body)
   self.assertIn("Proxmox",body)
   self.assertIn("10502",body)
   self.assertIn("Alexa",body)
   self.assertIn("waiting_for_home_assistant",body)
   self.assertEqual(headers.get("X-Content-Type-Options"),"nosniff")
   policy=headers.get("Content-Security-Policy")
   self.assertIn("frame-ancestors 'self'",policy)
   self.assertIn("connect-src 'self'",policy)
   self.assertIn("default-src 'none'",policy)
   self.assertIn("script-src 'self'",policy)
   self.assertNotIn("connect-src *",policy)
   self.assertNotIn("connect-src https:",policy)
   code,body,_=self.get("/?lang=en")
   self.assertEqual(code,200)
   self.assertIn("Getting started",body)
 def test_address_probe_requires_csrf_and_refuses_wrong_field(self):
  with patch.object(server,"probe_connection",return_value={"status":"tls_ok","detail":"tls_only"}) as probe:
   code,body=self.post({"csrf":server.CSRF,"action":"connection_probe",
                        "field":"public_audio_base","value":"https://tafa.example.org"})
   self.assertEqual(code,200)
   self.assertIn('"status":"tls_ok"',body)
   probe.assert_called_once()
   # JSON endpoints remain same-origin, authenticated and do not
   # loosen the browser's page policy.
   self.assertEqual(self.get("/?tab=connections")[0],200)
  code,_=self.post({"csrf":server.CSRF,"action":"connection_probe",
                    "field":"secret_token","value":"https://example.org"})
  self.assertEqual(code,400)
  code,_=self.post({"csrf":"bad","action":"connection_probe",
                    "field":"gpu_base","value":"http://192.168.1.5:10502"})
  self.assertEqual(code,403)
 def test_csrf_required(self):
  code,_=self.post({"csrf":"wrong","lang":"de"})
  self.assertEqual(code,403)
 def test_model_errors_visible(self):
  with patch.object(server,"status",return_value={"tablet_assist_for_alexa":"installed · 0.4.1"}),\
       patch.object(server,"speech_status",return_value={"piper_ready":False,"whisper_ready":False,"piper_phase":"error","whisper_phase":"error","piper_error":"RuntimeError: model unavailable","whisper_error":"ImportError: library unavailable"}),\
       patch.object(server,"setup_status",return_value={"status":"waiting_for_speech"}):
   code,body,_=self.get()
   self.assertEqual(code,200)
   self.assertIn("RuntimeError",body)
   self.assertIn("ImportError",body)
   self.assertIn("Sprachmodelle erneut laden",body)
 def test_install_confirmation_preserves_error_handling(self):
  with patch.object(server,"bootstrap",return_value=[]),\
       patch.object(server,"status",return_value={"tablet_assist_for_alexa":"installed · 0.4.0"}),\
       patch.object(server,"speech_status",return_value={"piper_ready":True,"whisper_ready":True}),\
       patch.object(server,"setup_status",return_value={"status":"configured"}):
   code,body=self.post({"csrf":server.CSRF,"lang":"de"})
   self.assertEqual(code,200)
   self.assertIn("Bestehende Dateien",body)
 def test_model_removal_requires_explicit_confirmation(self):
  with patch.object(server,"choose_speech_source",return_value=("external","http://192.168.1.10:5000")),\
       patch.object(server,"external_piper_ready",return_value=True),\
       patch.object(server,"local_model_inventory",return_value={"piper_bytes":1024,"whisper_bytes":2048}),\
       patch.object(server,"remove_local_models",return_value={"piper_bytes":1024,"whisper_bytes":2048}) as remove,\
       patch.object(server,"status",return_value={}),\
       patch.object(server,"setup_status",return_value={"status":"configured"}):
   code,_=self.post({"csrf":server.CSRF,"lang":"de","action":"cleanup","confirmation":"WRONG"})
   self.assertEqual(code,400)
   remove.assert_not_called()
   code,body=self.post({"csrf":server.CSRF,"lang":"de","action":"cleanup","confirmation":"ENTFERNEN"})
   self.assertEqual(code,200)
   self.assertIn("TAFA downloads removed",body)
   remove.assert_called_once_with("external")

if __name__=="__main__":unittest.main()
