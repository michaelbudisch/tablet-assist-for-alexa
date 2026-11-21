"""Local Piper-compatible TTS proxy. Only loopback clients may connect.
Configuration: a root-controlled JSON file containing worker_url, token, mode.
No extra audio/text persistence; no output beyond existing Piper processing.
"""
import http.server
import json
import os
import threading
import time
import urllib.parse
import urllib.request
import wave
import io

CONFIG = os.environ.get("JARVIS_TTS_CONFIG", "/etc/jarvis-tts-router.json")
BASE = "http://127.0.0.1:5000/synthesize"
MAX_WAV = 16 * 1024 * 1024
lock = threading.Lock()
retry_after = 0.0

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def request_wav(url, body, token=None, timeout=30):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-API-Key"] = token
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with opener.open(req, timeout=timeout) as response:
        data = response.read(MAX_WAV+1)
    if len(data) > MAX_WAV:
        raise ValueError("oversize audio")
    with wave.open(io.BytesIO(data), "rb") as audio:
        if audio.getnframes() <= 0:
            raise ValueError("empty audio")
    return data

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def send_bytes(self, status, data, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
    def do_POST(self):
        global retry_after
        if self.path != "/synthesize":
            self.send_bytes(404,b"not found", "text/plain"); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16384:
                raise ValueError()
            payload = json.loads(self.rfile.read(length))
            text = payload.get("text")
            if not isinstance(text,str) or not 0 < len(text.strip()) <= 500:
                raise ValueError()
            body = json.dumps({"text":text.strip()}, ensure_ascii=False).encode()
        except (ValueError, TypeError, AttributeError):
            self.send_bytes(400,b"invalid input", "text/plain"); return
        with lock:
            audio = None
            backend = "piper"
            try:
                with open(CONFIG, encoding="utf-8") as f:
                    cfg = json.load(f)
                worker = cfg.get("worker_url", "")
                token = cfg.get("token", "")
                url = urllib.parse.urlsplit(worker)
                import ipaddress
                ip = ipaddress.ip_address(url.hostname or "")
                if (cfg.get("mode") == "auto" and time.monotonic() >= retry_after
                    and url.scheme == "http" and url.port == 10501
                    and ip.version == 4 and any(ip in ipaddress.ip_network(n) for n in ("10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"))
                    and not url.username and not url.password and url.path in ("", "/") and not url.query and not url.fragment
                    and isinstance(token,str) and len(token)>=32):
                    try:
                        # Cheap readiness probe avoids waiting for a sleeping PC.
                        with opener.open(worker.rstrip("/")+"/health", timeout=1.5) as h:
                            health = json.loads(h.read(4096))
                        if health.get("ready") is not True or health.get("busy"):
                            raise RuntimeError()
                        audio = request_wav(worker.rstrip("/")+"/synthesize",body,token,timeout=18)
                        backend="qwen"
                        retry_after=0
                    except Exception:
                        retry_after=time.monotonic()+30
            except Exception:
                pass
            if audio is None:
                try:
                    audio=request_wav(BASE,body,timeout=40)
                except Exception:
                    self.send_bytes(503,b"both TTS services unavailable", "text/plain"); return
            print("TTS backend:",backend,flush=True)
        self.send_bytes(200,audio,"audio/wav")

if __name__ == "__main__":
    http.server.HTTPServer(("127.0.0.1",5002),Handler).serve_forever()
