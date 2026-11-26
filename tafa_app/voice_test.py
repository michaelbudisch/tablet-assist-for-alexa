"""Read-only diagnostics and explicitly initiated Assist speech tests.

No microphone recordings or conversation histories are written to disk. Only
TAFA Lokal can be invoked; no arbitrary pipeline, URL or Home Assistant action
is accepted from the browser. Supervisor credentials never leave this module.
"""
import json
import re
import secrets
import threading
import time
import urllib.request
from urllib.parse import urlsplit

WS_URL = "ws://supervisor/core/websocket"
MAX_AUDIO = 960000  # 30 seconds of 16kHz mono s16le, no arbitrary uploads.
_AUDIO_LOCK = threading.Lock()
_AUDIO_REFS = {}
_AUDIO_TTL = 180


class VoiceTestError(ValueError):
    """Safe, client-displayable validation or diagnostic failure."""


def _open_ws(token):
    if not token:
        raise VoiceTestError("Home Assistant authentication unavailable")
    from websockets.sync.client import connect
    ws = connect(WS_URL, open_timeout=5, close_timeout=2, max_size=2**21)
    try:
        hello = json.loads(ws.recv(timeout=6))
        if hello.get("type") == "auth_required":
            ws.send(json.dumps({"type": "auth", "access_token": token}))
            hello = json.loads(ws.recv(timeout=6))
        if hello.get("type") != "auth_ok":
            raise VoiceTestError("Home Assistant authentication failed")
        return ws
    except Exception:
        ws.close()
        raise


def _rpc(ws, ident, command, **arguments):
    ws.send(json.dumps({"id": ident, "type": command, **arguments}))
    for _ in range(15):
        answer = json.loads(ws.recv(timeout=9))
        if answer.get("id") == ident:
            if not answer.get("success"):
                raise VoiceTestError("Home Assistant rejected " + command)
            return answer.get("result")
    raise VoiceTestError("Home Assistant did not answer " + command)


def _tafa_pipeline(ws):
    response = _rpc(ws, 1, "assist_pipeline/pipeline/list")
    if not isinstance(response, dict):
        raise VoiceTestError("Assist pipelines unavailable")
    candidates = [
        item for item in (response.get("pipelines") or [])
        if isinstance(item, dict) and str(item.get("name", "")).casefold() == "tafa lokal"
        and isinstance(item.get("id"), str)
    ]
    if len(candidates) != 1:
        raise VoiceTestError("TAFA Lokal pipeline not configured")
    return candidates[0]


def voice_status(token):
    """Return actual registered router attributes; no guessed timing numbers."""
    with _open_ws(token) as ws:
        pipe = _tafa_pipeline(ws)
        registry = _rpc(ws, 2, "config/entity_registry/list")
        states = _rpc(ws, 3, "get_states")
    registry = registry if isinstance(registry, list) else []
    states = states if isinstance(states, list) else []
    by_id = {item.get("entity_id"): item for item in states if isinstance(item, dict)}
    suffixes = {"stt": "_stt_router", "tts": "_stream", "conversation": "_conversation_router"}
    result = {}
    for name, suffix in suffixes.items():
        matches = [item.get("entity_id") for item in registry
                   if isinstance(item, dict) and item.get("platform") == "tablet_assist_for_alexa"
                   and str(item.get("unique_id") or "").endswith(suffix)
                   and not item.get("disabled_by")]
        eid = matches[0] if len(matches) == 1 else None
        state = by_id.get(eid, {}) if eid else {}
        attrs = state.get("attributes") or {}
        result[name] = {
            "entity": eid or "",
            "state": str(state.get("state") or "unknown")[:60],
            "backend": str(attrs.get("letztes_backend") or "")[:90],
            "duration_ms": _number(attrs.get("letzte_dauer_ms")),
            "first_audio_ms": _number(attrs.get("erste_audio_ms")),
        }
    return {"pipeline": str(pipe["name"]), "pipeline_id": pipe["id"], "entities": result}


def _number(value):
    return round(value) if isinstance(value, (float, int)) and not isinstance(value, bool) and 0 <= value <= 300000 else None


def _tts_path(url):
    """Allow only Home Assistant's local TTS proxy output, no arbitrary URLs."""
    if not isinstance(url, str) or len(url) > 400:
        return ""
    parsed = urlsplit(url)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return ""
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return ""
    path = parsed.path
    if not re.fullmatch(r"/api/tts_proxy/[A-Za-z0-9_.~-]{1,200}", path):
        return ""
    return path


def _remember_audio(path):
    if not path:
        return ""
    now = time.monotonic()
    with _AUDIO_LOCK:
        for key in list(_AUDIO_REFS):
            if _AUDIO_REFS[key][1] <= now:
                _AUDIO_REFS.pop(key, None)
        identifier = secrets.token_urlsafe(18)
        _AUDIO_REFS[identifier] = (path, now + _AUDIO_TTL)
    return identifier


def load_audio(token, identifier):
    """Return bounded bytes from HA's own TTS proxy; no untrusted host access."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{12,40}", identifier):
        raise VoiceTestError("Invalid audio reference")
    with _AUDIO_LOCK:
        saved = _AUDIO_REFS.get(identifier)
        if saved and saved[1] < time.monotonic():
            _AUDIO_REFS.pop(identifier, None)
            saved = None
    if not saved:
        raise VoiceTestError("Audio expired")
    path = saved[0]
    req = urllib.request.Request("http://supervisor/core" + path, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=15) as res:
        kind = res.headers.get("Content-Type", "").split(";")[0].lower()
        if kind not in ("audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac"):
            raise VoiceTestError("Unexpected audio format")
        data = res.read(8*1024*1024+1)
        if not data or len(data) > 8*1024*1024:
            raise VoiceTestError("Audio size invalid")
        return data, kind


def run_voice(token, *, pcm=None, text=None, wake=False, conversation_id=""):
    """Run a user-initiated TAFA Lokal pipeline, recording per-stage event times.

    For speech, browser-provided 16kHz 16-bit mono PCM is streamed as binary
    after Home Assistant announces its STT handler. Never retain audio.
    """
    if (pcm is None) == (text is None):
        raise VoiceTestError("Supply exactly one audio or text input")
    if pcm is not None and (not isinstance(pcm, bytes) or len(pcm) % 2 or
                            not 16000 <= len(pcm) <= MAX_AUDIO):
        raise VoiceTestError("Audio must be 0.5-30 seconds, 16 kHz mono PCM")
    if text is not None and (not isinstance(text, str) or not 1 <= len(text.strip()) <= 300):
        raise VoiceTestError("Text must contain 1-300 characters")
    if conversation_id and (not isinstance(conversation_id, str) or
                            not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", conversation_id)):
        raise VoiceTestError("Invalid conversation ID")
    event_times = {}
    transcript = ""
    reply = ""
    audio_url = ""
    reported_conversation = ""
    start = time.monotonic()
    error = ""
    with _open_ws(token) as ws:
        pipeline = _tafa_pipeline(ws)
        command = {
            "id": 10, "type": "assist_pipeline/run", "pipeline": pipeline["id"],
            "start_stage": "stt" if pcm is not None else "intent",
            "end_stage": "stt" if wake else "tts",
            "input": {"sample_rate": 16000, "no_vad": True} if pcm is not None else {"text": text.strip()},
        }
        if conversation_id and not wake:
            command["conversation_id"] = conversation_id
        ws.send(json.dumps(command))
        handler = None
        sent = pcm is None
        done = False
        while time.monotonic() - start < 80:
            message = json.loads(ws.recv(timeout=75))
            if message.get("id") != 10:
                continue
            if message.get("type") == "result":
                if not message.get("success"):
                    raise VoiceTestError("Assist pipeline rejected the test")
                continue
            if message.get("type") != "event":
                continue
            event = message.get("event") or {}
            kind = event.get("type")
            data = event.get("data") or {}
            event_times[kind] = time.monotonic()
            if kind == "run-start":
                raw = (data.get("runner_data") or {}).get("stt_binary_handler_id")
                if isinstance(raw, int) and 0 <= raw <= 255:
                    handler = raw
            elif kind == "stt-start" and pcm is not None and not sent:
                if handler is None:
                    raise VoiceTestError("Assist did not provide an audio handler")
                for offset in range(0, len(pcm), 8192):
                    ws.send(bytes((handler,)) + pcm[offset:offset+8192])
                ws.send(bytes((handler,)))  # HA's end-of-stream marker.
                sent = True
            elif kind == "stt-end":
                transcript = str((data.get("stt_output") or {}).get("text") or "")[:500]
            elif kind == "intent-end":
                output = data.get("intent_output") or {}
                reply = str((((output.get("response") or {}).get("speech") or {}).get("plain") or {}).get("speech") or "")[:1000]
                reported_conversation = str(output.get("conversation_id") or "")[:128]
            elif kind == "tts-end":
                audio_url = str((data.get("tts_output") or {}).get("url") or "")
            elif kind == "error":
                error = str(data.get("message") or data.get("code") or "Assist pipeline error")[:180]
                done = True
                break
            elif kind == "run-end":
                done = True
                break
        if not done:
            raise VoiceTestError("Assist response timeout")
    def elapsed(begin, end):
        a, b = event_times.get(begin), event_times.get(end)
        return _number((b-a)*1000) if a is not None and b is not None and b >= a else None
    result = {
        "transcript": transcript, "reply": reply,
        "conversation_id": reported_conversation if re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", reported_conversation) else "",
        "audio_id": _remember_audio(_tts_path(audio_url)),
        "timings": {
            "stt_ms": elapsed("stt-start", "stt-end"),
            "intent_ms": elapsed("intent-start", "intent-end"),
            "tts_ms": elapsed("tts-start", "tts-end"),
            "total_ms": _number((time.monotonic()-start)*1000),
            "first_audio_ms": None,  # HA TTS entity reports actual first-byte latency.
        },
        "error": error,
        "pipeline": pipeline["name"],
    }
    return result
