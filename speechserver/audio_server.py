"""Only short-lived, unguessable MP3 files. Never proxy generation routes."""
import os
import re
import time
from pathlib import Path
from flask import Flask, abort, send_file
app = Flask(__name__)
AUDIO_DIR = Path(os.environ.get('JARVIS_AUDIO_DIR', '/var/lib/jarvis/audio'))
TTL = 900

@app.get('/<name>')
def audio(name):
    if not re.fullmatch(r'[a-f0-9]{32}\.mp3', name):
        abort(404)
    p = AUDIO_DIR / name
    try:
        if p.is_symlink() or not p.is_file() or time.time() - p.stat().st_mtime > TTL:
            abort(404)
        response = send_file(p, mimetype='audio/mpeg', conditional=True, max_age=0)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    except OSError:
        abort(404)
