"""Bundled, network-internal CPU Piper and Faster-Whisper service.

Only accepts bounded in-memory WAV or short text requests. Audio and transcripts
are never archived or logged. No public host port is mapped by the HA App.
"""
import io
import json
import logging
import subprocess
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG = logging.getLogger("tafa.speech")
DATA = Path("/data/tafa_speech")
VOICE_NAME = "de_DE-thorsten-medium"
MAX_AUDIO = 2_000_000
MAX_WAV = 16 * 1024 * 1024
MAX_REQUEST = MAX_AUDIO + 4096

class Models:
    def __init__(self):
        self.voice = None
        self.asr = None
        self.tts_error = "Initialisierung läuft"
        self.stt_error = "Initialisierung läuft"
        self.tts_phase = "initializing"
        self.stt_phase = "initializing"
        self._model_lock = threading.Lock()
        self.tts_lock = threading.BoundedSemaphore(1)
        self.stt_lock = threading.BoundedSemaphore(1)
    def load_voice(self):
        self.tts_phase = "loading"
        try:
            from piper import PiperVoice
            path = DATA / "voices" / (VOICE_NAME + ".onnx")
            config = path.with_suffix(path.suffix + ".json")
            if not (path.is_file() and config.is_file() and path.stat().st_size > 1_000_000):
                self.tts_phase = "downloading"
                path.parent.mkdir(parents=True, exist_ok=True)
                # Both model and .onnx.json are required. Existing partial downloads
                # are recoverable; the downloader validates the catalog entry.
                subprocess.run(
                    [sys.executable, "-m", "piper.download_voices", "--data-dir",
                     str(path.parent), VOICE_NAME],
                    check=True, timeout=1200,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                    text=True)
            if not (path.is_file() and config.is_file() and path.stat().st_size > 1_000_000):
                raise RuntimeError("Piper model or .onnx.json missing after download")
            self.tts_phase = "loading"
            self.voice = PiperVoice.load(str(path))
            self.tts_phase = "ready"
            self.tts_error = ""
            LOG.info("Piper voice ready (%s)", VOICE_NAME)
        except Exception as exc:
            self.voice = None
            self.tts_phase = "error"
            self.tts_error = type(exc).__name__ + ": " + str(exc)[:240]
            LOG.exception("Piper initialization failed (%s)", self.tts_error)
    def load_asr(self):
        self.stt_phase = "loading"
        try:
            from faster_whisper import WhisperModel
            folder = DATA / "models"
            folder.mkdir(parents=True, exist_ok=True)
            self.stt_phase = "downloading"
            self.asr = WhisperModel("base", device="cpu", compute_type="int8",
                                    download_root=str(folder))
            self.stt_phase = "ready"
            self.stt_error = ""
            LOG.info("Whisper CPU model ready")
        except Exception as exc:
            self.asr = None
            self.stt_phase = "error"
            self.stt_error = type(exc).__name__ + ": " + str(exc)[:240]
            LOG.exception("Whisper initialization failed (%s)", self.stt_error)
    def start(self):
        (DATA / "voices").mkdir(parents=True, exist_ok=True)
        threading.Thread(target=self.load_voice, daemon=True).start()
        threading.Thread(target=self.load_asr, daemon=True).start()
    def retry(self):
        """Start a new initialization only for a failed/unavailable model."""
        if not self._model_lock.acquire(blocking=False):
            return False
        try:
            if self.voice is None and self.tts_phase != "loading" and self.tts_phase != "downloading":
                threading.Thread(target=self.load_voice, daemon=True).start()
            if self.asr is None and self.stt_phase != "loading" and self.stt_phase != "downloading":
                threading.Thread(target=self.load_asr, daemon=True).start()
            return True
        finally:
            self._model_lock.release()

STATE = Models()

class Handler(BaseHTTPRequestHandler):
    server_version = "TAFA-Speech/0.2"
    def log_message(self, fmt, *args):
        # Never log request payload or user speech.
        LOG.debug("HTTP %s", self.path.split("?")[0])
    def send_data(self, payload, status=200, mime="application/json"):
        data = json.dumps(payload).encode() if isinstance(payload, dict) else payload
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == "/health":
            return self.send_data({"ready": STATE.voice is not None, "stt_ready": STATE.asr is not None})
        if self.path == "/status":
            return self.send_data({"piper_ready": STATE.voice is not None, "whisper_ready": STATE.asr is not None,
                                   "piper_error": STATE.tts_error, "whisper_error": STATE.stt_error,
                                   "piper_phase": STATE.tts_phase, "whisper_phase": STATE.stt_phase})
        self.send_data({"error":"unknown endpoint"},404)
    def do_POST(self):
        if self.path == "/retry":
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                return self.send_data({"error":"forbidden"},403)
            return self.send_data({"accepted":STATE.retry()})
        if self.path not in ("/synthesize", "/stt"):
            return self.send_data({"error":"unknown endpoint"},404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_data({"error":"invalid length"},400)
        if length <= 0 or length > MAX_REQUEST:
            return self.send_data({"error":"request size limit"},413)
        if self.path == "/synthesize":
            if STATE.voice is None:
                return self.send_data({"error":"piper not ready"},503)
            if not STATE.tts_lock.acquire(blocking=False):
                return self.send_data({"error":"tts busy"},429)
            try:
                if self.headers.get("Content-Type","").split(";")[0] != "application/json":
                    return self.send_data({"error":"JSON required"},415)
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                text = data.get("text") if isinstance(data,dict) else None
                if not isinstance(text,str) or not 0 < len(text.strip()) <= 500:
                    return self.send_data({"error":"invalid text"},400)
                out = io.BytesIO()
                with wave.open(out,"wb") as wav:
                    STATE.voice.synthesize_wav(text.strip(),wav)
                payload=out.getvalue()
                if len(payload)>MAX_WAV:
                    return self.send_data({"error":"audio size limit"},413)
                return self.send_data(payload,mime="audio/wav")
            except (ValueError,UnicodeError,RuntimeError,TypeError,KeyError):
                return self.send_data({"error":"tts failed"},500)
            finally:
                STATE.tts_lock.release()
        if STATE.asr is None:
            return self.send_data({"error":"whisper not ready"},503)
        if length > MAX_AUDIO:
            return self.send_data({"error":"audio size limit"},413)
        if not STATE.stt_lock.acquire(blocking=False):
            return self.send_data({"error":"stt busy"},429)
        try:
            if self.headers.get("Content-Type","").split(";")[0] != "audio/wav":
                return self.send_data({"error":"WAV required"},415)
            audio=self.rfile.read(length)
            if not audio.startswith(b"RIFF") or audio[8:12]!=b"WAVE":
                return self.send_data({"error":"invalid WAV"},400)
            segments, _ = STATE.asr.transcribe(io.BytesIO(audio),language="de",
                                               beam_size=2,vad_filter=True)
            result=" ".join(segment.text.strip() for segment in segments).strip()
            return self.send_data({"text":result[:2000]})
        except (ValueError,RuntimeError,TypeError,EOFError):
            return self.send_data({"error":"stt failed"},500)
        finally:
            STATE.stt_lock.release()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,format="%(levelname)s %(message)s")
    STATE.start()
    ThreadingHTTPServer(("0.0.0.0",5000),Handler).serve_forever()
