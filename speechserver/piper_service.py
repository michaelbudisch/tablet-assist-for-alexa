"""LAN-only Piper HTTP adapter implementing the existing /synthesize contract."""
import io
import os
import threading
import wave
from flask import Flask, jsonify, request, Response
from piper import PiperVoice

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8192
voice = PiperVoice.load(os.environ['JARVIS_PIPER_MODEL'])
lock = threading.Lock()

@app.get('/health')
def health():
    return jsonify(ready=True)

@app.post('/synthesize')
def synthesize():
    data = request.get_json(silent=True)
    text = data.get('text') if isinstance(data, dict) else None
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 500:
        return jsonify(error='Invalid text'), 400
    try:
        out = io.BytesIO()
        with lock, wave.open(out, 'wb') as wav:
            voice.synthesize_wav(text.strip(), wav)
        audio = out.getvalue()
        if len(audio) > 16 * 1024 * 1024:
            return jsonify(error='Audio too large'), 413
        return Response(audio, mimetype='audio/wav')
    except Exception:
        app.logger.error('Synthesis failed')
        return jsonify(error='Synthesis failed'), 500
