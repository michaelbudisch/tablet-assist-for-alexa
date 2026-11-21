"""LAN-only Qwen TTS, standard model voices, no persistent audio or text logs."""
import hmac
import io
import os
import threading
import time

import soundfile as sf
import torch
from flask import Flask, Response, jsonify, request
from qwen_tts import Qwen3TTSModel
from waitress import serve

TOKEN = os.environ.get("JARVIS_TTS_TOKEN", "")
if len(TOKEN) < 32:
    raise RuntimeError("A random JARVIS_TTS_TOKEN of at least 32 characters is required")
MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
SPEAKER = os.environ.get("QWEN_SPEAKER", "Ryan")
if not torch.cuda.is_available():
    raise RuntimeError("NVIDIA CUDA is not available; check Docker GPU support")
print("Loading Qwen model:", MODEL, flush=True)
model = Qwen3TTSModel.from_pretrained(MODEL, device_map="cuda:0", dtype=torch.bfloat16, attn_implementation="sdpa")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384
lock = threading.Lock()

@app.get("/health")
def health():
    return jsonify(ready=True, backend="qwen", model=MODEL, speaker=SPEAKER, busy=lock.locked())

@app.post("/synthesize")
def synthesize():
    if not hmac.compare_digest(request.headers.get("X-API-Key", ""), TOKEN):
        return jsonify(error="unauthorized"), 401
    data = request.get_json(silent=True)
    text = data.get("text") if isinstance(data, dict) else None
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 500:
        return jsonify(error="text must contain 1-500 characters"), 400
    if not lock.acquire(blocking=False):
        return jsonify(error="busy"), 503
    started = time.monotonic()
    try:
        if MODEL.endswith("VoiceDesign"):
            wavs, rate = model.generate_voice_design(text=text.strip(), language="German", instruct="A calm, clear, warm adult male voice speaking standard German, natural pacing.", max_new_tokens=2048)
        else:
            wavs, rate = model.generate_custom_voice(text=text.strip(), language="German", speaker=SPEAKER, max_new_tokens=2048)
        out = io.BytesIO()
        sf.write(out, wavs[0], rate, format="WAV", subtype="PCM_16")
        print(f"Synthesis completed in {time.monotonic()-started:.2f}s", flush=True)
        return Response(out.getvalue(), mimetype="audio/wav", headers={"Cache-Control":"no-store"})
    except Exception:
        print("Qwen synthesis failed", flush=True)
        return jsonify(error="synthesis failed"), 503
    finally:
        lock.release()

if __name__ == "__main__":
    print("Qwen ready on port 10501", flush=True)
    serve(app, host="0.0.0.0", port=10501, threads=2)
