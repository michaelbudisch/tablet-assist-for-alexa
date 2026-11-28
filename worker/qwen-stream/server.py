"""Private-LAN Faster Qwen TTS: PCM stream and complete WAV endpoints."""
import gc
import hashlib
import io
import os
import threading
import time
import wave

import numpy as np
import torch
from flask import Flask, Response, jsonify, request
from faster_qwen3_tts import FasterQwen3TTS
from waitress import serve
from text_processing import dictionary, prepare_text, split_sentences

MODE = os.environ.get('STREAM_VOICE_MODE', 'fast').strip().lower()
MODELS = {
    'fast': 'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',
    'styled': 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice',
    'design': 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',
    'fixed': 'Qwen/Qwen3-TTS-12Hz-1.7B-Base',
}
if MODE not in MODELS:
    raise RuntimeError('STREAM_VOICE_MODE must be fast, styled, design or fixed')
FIXED_SIZE = os.environ.get('STREAM_FIXED_MODEL_SIZE', '1.7B').strip().upper()
if MODE == 'fixed' and FIXED_SIZE not in ('0.6B', '1.7B'):
    raise RuntimeError('STREAM_FIXED_MODEL_SIZE must be 0.6B or 1.7B')
MODEL = f'Qwen/Qwen3-TTS-12Hz-{FIXED_SIZE}-Base' if MODE == 'fixed' else MODELS[MODE]

STYLE = os.environ.get('STREAM_VOICE_STYLE', 'A mature male voice with a warm low-mid register, calm and precise delivery, clear natural German diction, subtle British-influenced cadence, restrained dry wit, and a professional, composed tone. Moderate pace; no theatrical exaggeration.').strip()
if MODE != 'fast' and not 0 < len(STYLE) <= 1000:
    raise RuntimeError('STREAM_VOICE_STYLE must contain 1 to 1000 characters')
SPEAKER = os.environ.get('QWEN_SPEAKER', 'Ryan')
from pathlib import Path
from reference_voice import REFERENCE_TEXT, ensure_reference, valid_reference
from voice_variants import CHOICES, inventory, reference_id, variant_path, variant_style
REFERENCE = None
VOICE_ID = None
variant = None
if MODE == 'fixed':
    variant = os.environ.get('STREAM_VOICE_VARIANT', '1').strip()
    if not 0 < len(variant) <= 80:
        raise RuntimeError('STREAM_VOICE_VARIANT must contain 1 to 80 characters')
    VOICE_ID = hashlib.sha256(('v1\n' + STYLE + '\n' + variant + '\n' + REFERENCE_TEXT).encode('utf-8')).hexdigest()[:24]

RATE = 24000
MAX_BYTES = 16 * 1024 * 1024
if not torch.cuda.is_available():
    raise RuntimeError('CUDA unavailable')
if MODE == 'fixed':
    REFERENCE = ensure_reference(VOICE_ID, STYLE)
print(f'Loading Faster Qwen: {MODE} ({MODEL})', flush=True)
model = FasterQwen3TTS.from_pretrained(MODEL)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16384
lock = threading.Lock()
cancel_event = threading.Event()
voice_job = {'state': 'idle', 'variant': None, 'updated_at': 0}
SPEECH_CLEANUP = os.environ.get('STREAM_TEXT_CLEANUP', '1') == '1'
SPEECH_SPLIT = os.environ.get('STREAM_SPEECH_SPLIT', '0') == '1'
PRONUNCIATION = dictionary(os.environ.get('STREAM_PRONUNCIATION', ''))


def requested_reference(data):
    if MODE != 'fixed':
        return None, '', 'mode-not-fixed'
    selected = data.get('voice_variant') if isinstance(data, dict) else None
    if selected is None or selected == 'default':
        return REFERENCE, variant, 'default'
    if not isinstance(selected, str) or selected not in CHOICES:
        return REFERENCE, variant, 'invalid-variant'
    path = variant_path(selected, STYLE)
    if valid_reference(path):
        return path, selected, 'selected'
    return REFERENCE, variant, 'not-prepared'


def voice_headers(selection):
    _, effective, status = selection
    # Limit the optional user-facing header to numeric, known variants.
    return {'X-TAFA-Voice-Variant': effective if effective in CHOICES else 'default',
            'X-TAFA-Voice-Status': status}


def pcm_chunks(text, ref=None):
    total = 0
    segments = split_sentences(text, 180) if SPEECH_SPLIT and len(text) > 180 else [text]
    for sentence in segments:
        if cancel_event.is_set():
            return
        kwargs = dict(text=sentence, language='German', chunk_size=8)
        if MODE == 'fixed':
            iterator = model.generate_voice_clone_streaming(
                **kwargs, ref_audio=str(ref or REFERENCE), ref_text=REFERENCE_TEXT,
                xvec_only=False, non_streaming_mode=True,
            )
        elif MODE == 'design':
            iterator = model.generate_voice_design_streaming(**kwargs, instruct=STYLE)
        else:
            if MODE == 'styled':
                kwargs['instruct'] = STYLE
            iterator = model.generate_custom_voice_streaming(**kwargs, speaker=SPEAKER)
        for audio, rate, _timing in iterator:
            if cancel_event.is_set():
                return
            if rate != RATE:
                raise ValueError('Unexpected sample rate')
            data = np.asarray(audio, dtype=np.float32).reshape(-1)
            if not data.size:
                continue
            if not np.isfinite(data).all():
                raise ValueError('Invalid sample')
            pcm = (np.clip(data, -1.0, 1.0) * 32767).astype('<i2').tobytes()
            total += len(pcm)
            if total > MAX_BYTES:
                raise ValueError('Audio exceeds size limit')
            yield pcm

def prepare_voice(number):
    """Prepare one synthetic reference without a second TTS model in VRAM."""
    global model, voice_job
    state = 'error'
    try:
        # Synthesis shares the same lock. Release the Base model BEFORE the
        # one-time VoiceDesign subprocess uses the GPU; retain the Ollama model.
        model = None
        gc.collect()
        torch.cuda.empty_cache()
        ensure_reference(reference_id(number, STYLE), variant_style(number, STYLE))
        state = 'ready'
    except Exception as exc:
        print('Voice preparation failed:', type(exc).__name__, flush=True)
    finally:
        try:
            # Even if preparation fails, restore the original streaming model.
            model = FasterQwen3TTS.from_pretrained(MODEL)
        except Exception as exc:
            print('Qwen reload failed:', type(exc).__name__, flush=True)
            model = None
            state = 'error'
        voice_job = {'state': state, 'variant': number, 'updated_at': int(time.time())}
        lock.release()


@app.get('/voices')
def voices():
    return jsonify(available=MODE == 'fixed', mode=MODE,
                   default_variant=variant if MODE == 'fixed' else 'default',
                   variants=inventory(STYLE, MODE),
                   job=dict(voice_job), busy=lock.locked())


@app.post('/voices/prepare')
def voices_prepare():
    data = request.get_json(silent=True)
    number = data.get('variant') if isinstance(data, dict) and set(data) == {'variant'} else None
    if not isinstance(number, str) or number not in CHOICES:
        return jsonify(error='invalid variant'), 400
    if MODE != 'fixed':
        return jsonify(error='fixed mode required'), 409
    if not lock.acquire(blocking=False):
        return jsonify(error='worker busy'), 409
    started = False
    try:
        if valid_reference(variant_path(number, STYLE)):
            voice_job.update(state='ready', variant=number, updated_at=int(time.time()))
            return jsonify(state='ready', variant=number)
        voice_job.update(state='preparing', variant=number, updated_at=int(time.time()))
        threading.Thread(target=prepare_voice, args=(number,), daemon=True).start()
        started = True
        return jsonify(state='preparing', variant=number), 202
    finally:
        # Never unlock a running worker; avoid races when it finishes quickly.
        if not started:
            lock.release()


@app.get('/health')
def health():
    return jsonify(ready=model is not None and not lock.locked(), worker_version='2.2.8',
                   backend='faster-qwen', busy=lock.locked(), rate=RATE, model=MODEL,
                   voice_mode=MODE, speaker=SPEAKER if MODE in ('fast', 'styled') else None,
                   voice_id=VOICE_ID, speech_cleanup=SPEECH_CLEANUP,
                   sentence_splitting=SPEECH_SPLIT, supports_cancel=True,
                   supports_voice_management=MODE == 'fixed')


def validated_text():
    data = request.get_json(silent=True)
    text = data.get('text') if isinstance(data, dict) else None
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 500:
        return None, (jsonify(error='invalid text'), 400)
    try:
        return prepare_text(text.strip(), PRONUNCIATION) if SPEECH_CLEANUP else text.strip(), None
    except ValueError:
        return None, (jsonify(error='invalid processed speech text'), 400)


@app.post('/cancel')
def cancel():
    # Cooperative cancellation. Playback clients must still stop their own
    # audio; an active GPU generation can only stop between generated chunks.
    busy = lock.locked()
    if busy:
        cancel_event.set()
    return jsonify(cancel_requested=busy, worker_version='2.2.8'), 202


@app.post('/stream')
def stream():
    text, error = validated_text()
    if error is not None:
        return error
    if not lock.acquire(blocking=False):
        return jsonify(error='busy'), 503
    cancel_event.clear()
    start = time.monotonic()
    selection = requested_reference(request.get_json(silent=True))
    iterator = pcm_chunks(text, selection[0])
    # Generate one playable chunk before returning HTTP 200. This allows
    # clients to fall back safely if initialization or synthesis fails.
    try:
        first = next(iterator)
    except Exception:
        iterator.close()
        lock.release()
        print('Streaming initialization failed', flush=True)
        return jsonify(error='synthesis failed'), 503
    print(f'First audio: {time.monotonic()-start:.3f}s', flush=True)
    released = False

    def cleanup():
        nonlocal released
        if not released:
            released = True
            try:
                iterator.close()
            finally:
                lock.release()

    def body():
        try:
            if not cancel_event.is_set():
                yield first
            for chunk in iterator:
                if cancel_event.is_set():
                    break
                yield chunk
            print(f'Stream completed: {time.monotonic()-start:.3f}s', flush=True)
        finally:
            cleanup()
    response = Response(body(), mimetype='application/octet-stream', headers={
        'Cache-Control': 'no-store', 'X-Audio-Rate': str(RATE),
        'X-Audio-Format': 's16le-mono', 'X-Accel-Buffering': 'no',
        **voice_headers(selection),
    })
    response.call_on_close(cleanup)
    return response


@app.post('/synthesize')
def synthesize():
    text, error = validated_text()
    if error is not None:
        return error
    if not lock.acquire(blocking=False):
        return jsonify(error='busy'), 503
    try:
        cancel_event.clear()
        selection = requested_reference(request.get_json(silent=True))
        pcm = b''.join(pcm_chunks(text, selection[0]))
        if cancel_event.is_set():
            return jsonify(error='synthesis cancelled'), 503
        if not pcm:
            raise ValueError('No audio')
        out = io.BytesIO()
        with wave.open(out, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(RATE)
            w.writeframes(pcm)
        return Response(out.getvalue(), mimetype='audio/wav', headers={'Cache-Control': 'no-store', **voice_headers(selection)})
    except Exception:
        print('Synthesis failed', flush=True)
        return jsonify(error='synthesis failed'), 503
    finally:
        lock.release()


if __name__ == '__main__':
    # First request can be slower due to CUDA graph capture.
    print('Faster Qwen ready on port 10502', flush=True)
    serve(app, host='0.0.0.0', port=10502, threads=3, log_socket_errors=False)
