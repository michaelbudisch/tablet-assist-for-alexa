"""Jarvis MP3 API v2: GPU WAV or local Piper, same Alexa file interface."""
import os
import uuid
import json
import hmac
import time
import hashlib
import re
import math
import io
import wave
import subprocess
import threading
import urllib.request
from collections import OrderedDict
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8192
AUDIO_DIR = Path(os.environ.get('JARVIS_AUDIO_DIR', '/var/lib/jarvis/audio'))
PIPER_URL = os.environ.get('JARVIS_PIPER_URL', 'http://127.0.0.1:5000/synthesize')
GPU_BASE = os.environ.get('JARVIS_GPU_BASE', '').rstrip('/')
API_TOKEN = os.environ['PIPER_API_TOKEN']
if len(API_TOKEN) < 32:
    raise RuntimeError('Set a random PIPER_API_TOKEN of at least 32 characters')
GPU_TOKEN = os.environ.get('JARVIS_TTS_TOKEN', '')
MAX_WAV = 16 * 1024 * 1024
MAX_ITEMS = 32
MAX_CACHED_MP3 = 2 * 1024 * 1024
CACHE = OrderedDict()
LOCK = threading.Lock()

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

def fetch(url, payload=None, token='', timeout=10, limit=MAX_WAV):
    headers = {'Content-Type': 'application/json'} if payload is not None else {}
    if token:
        headers['X-API-Key'] = token
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8') if payload is not None else None, headers=headers)
    with HTTP.open(req, timeout=timeout) as resp:
        result = resp.read(limit+1)
        if len(result) > limit or resp.status != 200:
            raise ValueError('Invalid response')
        return result, resp.headers

GPU_WAIT_SECONDS = 8.0


def gpu_state():
    if not GPU_TOKEN or not GPU_BASE:
        return 'not_configured'
    try:
        data, _ = fetch(GPU_BASE+'/health', timeout=1.5, limit=65536)
        result = json.loads(data)
        if not isinstance(result, dict):
            return 'unavailable'
        if result.get('busy'):
            return 'busy'
        return 'ready' if result.get('ready') is True else 'not_ready'
    except Exception:
        return 'unavailable'


def wait_for_gpu(deadline):
    while True:
        state = gpu_state()
        if state != 'busy':
            return state
        left = deadline - time.monotonic()
        if left <= 0:
            return 'busy_timeout'
        time.sleep(min(0.4, left))


def gpu_audio(text, variant, chime, sound_profile):
    deadline = time.monotonic() + GPU_WAIT_SECONDS
    state = wait_for_gpu(deadline)
    if state != 'ready':
        return None, state
    try:
        return get_audio(text, 'Faster Qwen', variant, chime, sound_profile), ''
    except Exception as exc:
        # Retry only a quick rejection if the worker is busy or explicitly
        # reports a temporary HTTP conflict. Never retry a long timeout.
        code = getattr(exc, 'code', None)
        if time.monotonic() < deadline:
            state = gpu_state()
            if state == 'busy' or (code in (409, 429, 503) and state == 'ready'):
                time.sleep(min(0.4, max(0, deadline-time.monotonic())))
                state = wait_for_gpu(deadline) if time.monotonic() < deadline else 'busy_timeout'
                if state == 'ready' and time.monotonic() < deadline:
                    try:
                        return get_audio(text, 'Faster Qwen', variant, chime, sound_profile), ''
                    except Exception:
                        return None, 'gpu_retry_failed'
                return None, state if state != 'ready' else 'busy_timeout'
        return None, 'gpu_synthesis_failed'


# Amazon SSML requires MPEG-2, 48 kbit/s, 24 kHz or lower.
# Original GPU signal is mono. Prefer a single channel without stereo upmix.
MP3_CHANNELS = 1  # Set to 2 only if an Echo rejects mono MP3.


def speech_gain(wav):
    """A bounded, static gain; no aggressive compression or pitch changes."""
    result = subprocess.run(['ffmpeg','-nostdin','-hide_banner','-i','pipe:0',
        '-ac','1','-af','volumedetect','-f','null','-'], input=wav,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=15)
    stats = result.stderr.decode('utf-8','replace')
    mean = re.search(r'mean_volume:\s*(-?[\d.]+) dB',stats)
    peak = re.search(r'max_volume:\s*(-?[\d.]+) dB',stats)
    if not mean or not peak:
        return 0.0
    rms, maximum = float(mean.group(1)), float(peak.group(1))
    if not math.isfinite(rms) or not math.isfinite(maximum) or maximum <= -60:
        return 0.0
    # Moderate level adjustment, leaving peak headroom for MP3 encoding.
    return min(4.0, max(-4.0, -20.0-rms), -2.0-maximum)


SOUND_PROFILES = ('Natürlich', 'Studio', 'Durchsage')


def speech_filters(gain, sound_profile):
    # Preserve version 2.2.0 exactly in the default profile.
    volume = f'volume={gain:.2f}dB'
    if sound_profile == 'Natürlich':
        return volume
    if sound_profile == 'Studio':
        return (f'{volume},highpass=f=65,equalizer=f=180:t=q:w=0.9:g=1,'
                'equalizer=f=2600:t=q:w=0.9:g=1.5,'
                'acompressor=threshold=0.10:ratio=1.5:attack=15:release=150:makeup=1.12:knee=2.8,'
                'alimiter=limit=0.79:attack=5:release=80:level=0:latency=1')
    if sound_profile == 'Durchsage':
        return (f'{volume},highpass=f=85,equalizer=f=230:t=q:w=0.9:g=-1.5,'
                'equalizer=f=2800:t=q:w=1:g=2,'
                'acompressor=threshold=0.09:ratio=2:attack=12:release=120:makeup=1.22:knee=2.8,'
                'alimiter=limit=0.79:attack=5:release=80:level=0:latency=1')
    raise ValueError('Invalid sound profile')


def encode_mp3(wav, chime=False, sound_profile='Natürlich'):
    if len(wav) < 44 or wav[:4] != b'RIFF' or wav[8:12] != b'WAVE':
        raise ValueError('Invalid WAV')
    gain = speech_gain(wav)
    speech = speech_filters(gain, sound_profile)
    layout = 'mono' if MP3_CHANNELS == 1 else 'stereo'
    fmt = f'aformat=sample_rates=24000:channel_layouts={layout}'
    args = ['ffmpeg','-nostdin','-y','-loglevel','error','-i','pipe:0']
    if chime:
        args += ['-f','lavfi','-i','sine=frequency=880:sample_rate=24000:duration=0.18',
                 '-f','lavfi','-i','sine=frequency=1175:sample_rate=24000:duration=0.22',
                 '-filter_complex',
                 f'[1:a]volume=0.70,afade=t=in:d=0.02,afade=t=out:st=0.12:d=0.06,{fmt}[a];'
                 f'[2:a]volume=0.58,afade=t=in:d=0.02,afade=t=out:st=0.15:d=0.07,apad=pad_dur=0.24,{fmt}[b];'
                 f'[0:a]{speech},{fmt}[c];[a][b][c]concat=n=3:v=0:a=1[out]',
                 '-map','[out]']
    else:
        args += ['-map','0:a:0','-af',speech]
    args += ['-ac',str(MP3_CHANNELS),'-ar','24000','-codec:a','libmp3lame','-b:a','48k',
             '-compression_level','0','-write_xing','0','-map_metadata','-1','-f','mp3','pipe:1']
    result = subprocess.run(args, input=wav, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, timeout=25)
    if not result.stdout:
        raise ValueError('Empty MP3')
    return result.stdout


def fetch_jarvis_stream(text, variant):
    # Same synthesis route and audio format as native Jarvis Assist.
    payload = json.dumps({'text': text, 'voice_variant': variant}).encode('utf-8')
    req = urllib.request.Request(GPU_BASE+'/stream', data=payload,
        headers={'Content-Type':'application/json','X-API-Key':GPU_TOKEN}, method='POST')
    deadline = time.monotonic() + 45
    pcm = bytearray()
    with HTTP.open(req, timeout=15) as response:
        headers = response.headers
        if response.status != 200 or headers.get('X-Audio-Rate') != '24000' or headers.get('X-Audio-Format') != 's16le-mono':
            raise ValueError('Invalid GPU stream format')
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError('GPU stream deadline exceeded')
            chunk = response.read1(8192)
            if not chunk:
                break
            pcm.extend(chunk)
            if len(pcm) > MAX_WAV-44:
                raise ValueError('GPU stream too large')
    if not pcm or len(pcm) % 2:
        raise ValueError('Empty or malformed GPU PCM')
    # Create a valid WAV with exact lengths, preserving the original sample rate.
    out = io.BytesIO()
    with wave.open(out,'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(pcm)
    return out.getvalue(), headers


def get_audio(text, backend, variant, chime=False, sound_profile='Natürlich'):
    key = (backend, variant if backend == 'Faster Qwen' else 'Thorsten', hashlib.sha256(text.encode()).hexdigest(), chime, sound_profile)
    now = time.monotonic()
    with LOCK:
        for k, entry in list(CACHE.items()):
            if entry[0] <= now:
                CACHE.pop(k, None)
        if key in CACHE:
            CACHE.move_to_end(key)
            _, mp3, effective = CACHE[key]
            return mp3, effective, True
    if backend == 'Faster Qwen':
        wav, headers = fetch_jarvis_stream(text, variant)
        effective = headers.get('X-Jarvis-Voice-Variant', 'default')
        if effective not in {'default', *map(str, range(1, 10))}:
            effective = 'default'
        cacheable = effective == variant
        ttl = 600
    else:
        wav, _ = fetch(PIPER_URL, {'text': text}, timeout=60)
        effective, cacheable, ttl = 'Thorsten', True, 3600
    mp3 = encode_mp3(wav, chime, sound_profile)
    if cacheable and len(mp3) <= MAX_CACHED_MP3:
        with LOCK:
            CACHE[key] = (time.monotonic()+ttl, mp3, effective)
            CACHE.move_to_end(key)
            while len(CACHE) > MAX_ITEMS:
                CACHE.popitem(last=False)
    return mp3, effective, False

@app.get('/health')
def health():
    return jsonify(status='online', version='2.3.0', sound_profiles=list(SOUND_PROFILES), mp3_channels=MP3_CHANNELS, mp3_bitrate=48000, mp3_rate=24000, gpu_configured=bool(GPU_TOKEN and GPU_BASE))

@app.post('/generate')
def generate():
    started = time.monotonic()
    if not hmac.compare_digest(request.headers.get('X-API-Key','').encode(), API_TOKEN.encode()):
        return jsonify(error='Unauthorized'), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='JSON fehlt'), 400
    text = data.get('text', '')
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 500:
        return jsonify(error='Text fehlt oder zu lang'), 400
    text = text.strip()
    sound_profile = data.get('sound_profile', 'Natürlich')
    if not isinstance(sound_profile, str) or sound_profile not in SOUND_PROFILES:
        return jsonify(error='Ungueltiges Klangprofil'), 400
    chime = data.get('chime', False)
    if not isinstance(chime, bool):
        return jsonify(error='Ungueltiger Signalton-Wert'), 400
    profile = data.get('profile', 'Automatisch')
    variant = data.get('voice_variant', 'default')
    if profile not in ('Automatisch', 'Homeserver') or not isinstance(variant,str) or variant not in {'default', *map(str,range(1,10))}:
        return jsonify(error='Ungueltiges Profil oder Stimme'), 400
    filename = uuid.uuid4().hex+'.mp3'
    temporary = AUDIO_DIR/(filename+'.tmp')
    backend = 'Piper'
    fallback = False
    fallback_reason = ''
    try:
        result_gpu = None
        if profile == 'Automatisch':
            result_gpu, fallback_reason = gpu_audio(text, variant, chime, sound_profile)
        if result_gpu is not None:
            mp3, effective, cached = result_gpu
            backend = 'Faster Qwen'
        else:
            fallback = profile == 'Automatisch'
            if fallback:
                app.logger.info('GPU fallback: %s', fallback_reason)
            mp3, effective, cached = get_audio(text, 'Piper', variant, chime, sound_profile)
        temporary.write_bytes(mp3)
        temporary.replace(AUDIO_DIR/filename)
        for old in AUDIO_DIR.glob('*.mp3'):
            try:
                if len(old.stem)==32 and all(x in '0123456789abcdef' for x in old.stem) and time.time()-old.stat().st_mtime > 900:
                    old.unlink(missing_ok=True)
            except OSError:
                pass
        result = jsonify(success=True, filename=filename, path='/'+filename, backend=backend, audio_source='stream' if backend=='Faster Qwen' else 'piper', mp3_channels=MP3_CHANNELS, mp3_bitrate=48000, mp3_rate=24000, voice_variant=effective, cached=cached, fallback=fallback, fallback_reason=fallback_reason, chime=chime, sound_profile=sound_profile, duration_ms=round((time.monotonic()-started)*1000))
        result.headers['X-Piper-Cache'] = 'HIT' if cached else 'MISS'
        return result
    except Exception:
        app.logger.error('MP3 generation failed')
        return jsonify(error='Audioerzeugung fehlgeschlagen'), 500
    finally:
        temporary.unlink(missing_ok=True)
