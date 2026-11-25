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
   self.assertIn("waiting_for_home_assistant",body)
   self.assertEqual(headers.get("X-Content-Type-Options"),"nosniff")
   self.assertIn("frame-ancestors 'self'",headers.get("Content-Security-Policy"))
   code,body,_=self.get("/?lang=en")
   self.assertEqual(code,200)
   self.assertIn("Getting started",body)
 def test_csrf_required(self):
  code,_=self.post({"csrf":"wrong","lang":"de"})
  self.assertEqual(code,403)
 def test_install_confirmation_preserves_error_handling(self):
  with patch.object(server,"bootstrap",return_value=[]),\
       patch.object(server,"status",return_value={"tablet_assist_for_alexa":"installed · 0.4.0"}),\
       patch.object(server,"speech_status",return_value={"piper_ready":True,"whisper_ready":True}),\
       patch.object(server,"setup_status",return_value={"status":"configured"}):
   code,body=self.post({"csrf":server.CSRF,"lang":"de"})
   self.assertEqual(code,200)
   self.assertIn("Bestehende Dateien",body)
if __name__=="__main__":unittest.main()
