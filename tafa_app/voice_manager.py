"""LAN-only TAFA voice management proxy for the Supervisor Ingress UI.

Only the configured GPU worker is contacted. This module never accesses the
filesystem or controls Docker on a different computer.
"""
import json
import urllib.error
from urllib.request import Request

from speech_source import HTTP, load_supervisor_options, private_http_origin

CHOICES = tuple(str(i) for i in range(1, 10))
PREVIEW_TEXT = "Guten Tag. Dies ist eine kurze Hörprobe meiner Stimme. Ich spreche jetzt mit der ausgewählten Variante."
MAX_AUDIO = 2 * 1024 * 1024


class VoiceManagerError(RuntimeError):
    def __init__(self, message, status=503):
        super().__init__(message)
        self.status = status


def _base(token):
    options = load_supervisor_options(token)
    address = options.get("gpu_base", "")
    if not address:
        raise VoiceManagerError("GPU worker not configured", 409)
    try:
        return private_http_origin(address)
    except ValueError:
        raise VoiceManagerError("Invalid GPU worker address", 409) from None


def _request(token, path, payload=None, timeout=5, limit=32768):
    address = _base(token) + path
    if payload is None:
        request = Request(address, method="GET")
    else:
        request = Request(address, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json"}, method="POST")
    try:
        with HTTP.open(request, timeout=timeout) as response:
            body = response.read(limit + 1)
            if len(body) > limit:
                raise VoiceManagerError("GPU worker reply too large", 502)
            return body, response.headers, response.status
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise VoiceManagerError("GPU worker update required (voice API unavailable)", 409) from None
        if exc.code == 409:
            raise VoiceManagerError("Voice mode unsupported or GPU worker busy", 409) from None
        if exc.code == 400:
            raise VoiceManagerError("Invalid voice variant", 400) from None
        raise VoiceManagerError("GPU worker request failed", 503) from None
    except (TimeoutError, OSError, ValueError):
        raise VoiceManagerError("GPU worker not reachable", 503) from None


def catalog(token):
    body, _, _ = _request(token, "/voices", timeout=3)
    try:
        raw = json.loads(body)
    except (ValueError, UnicodeError):
        raise VoiceManagerError("Invalid GPU voice inventory", 502) from None
    if not isinstance(raw, dict) or not isinstance(raw.get("variants"), list):
        raise VoiceManagerError("Invalid GPU voice inventory", 502)
    variants = []
    received = {}
    for item in raw["variants"]:
        if isinstance(item, dict) and item.get("id") in CHOICES:
            received[item["id"]] = item
    for number in CHOICES:
        row = received.get(number, {})
        variants.append({
            "id": number,
            "name_de": str(row.get("name_de") or number)[:60],
            "name_en": str(row.get("name_en") or number)[:60],
            "ready": row.get("ready") is True,
        })
    job = raw.get("job") if isinstance(raw.get("job"), dict) else {}
    state = job.get("state", "idle")
    return {
        "available": raw.get("available") is True,
        "mode": raw.get("mode") if raw.get("mode") in ("fast", "styled", "design", "fixed") else "unknown",
        "default_variant": str(raw.get("default_variant", "default"))[:20],
        "busy": raw.get("busy") is True,
        "job": {"state": state if state in ("idle", "preparing", "ready", "error") else "idle",
                "variant": job.get("variant") if job.get("variant") in CHOICES else None},
        "variants": variants,
        "selected": str(load_supervisor_options(token).get("voice_variant", "default")),
    }


def prepare(token, number):
    if number not in CHOICES or not isinstance(number, str):
        raise VoiceManagerError("Invalid voice variant", 400)
    raw, _, _ = _request(token, "/voices/prepare", {"variant": number}, timeout=5)
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        raise VoiceManagerError("Invalid worker preparation status", 502) from None
    if not isinstance(result, dict) or result.get("state") not in ("ready", "preparing"):
        raise VoiceManagerError("Unexpected worker preparation status", 502)
    return {"state": result["state"], "variant": number}


def preview(token, number):
    if number not in (*CHOICES, "default") or not isinstance(number, str):
        raise VoiceManagerError("Invalid voice variant", 400)
    info = catalog(token)
    if number != "default":
        if not info["available"]:
            raise VoiceManagerError("Fixed voice mode required", 409)
        if not any(x["id"] == number and x["ready"] for x in info["variants"]):
            raise VoiceManagerError("Prepare this voice before preview", 409)
    audio, headers, _ = _request(token, "/synthesize",
        {"text": PREVIEW_TEXT, "voice_variant": number}, timeout=90, limit=MAX_AUDIO)
    if not audio.startswith(b"RIFF") or audio[8:12] != b"WAVE":
        raise VoiceManagerError("Worker returned no playable WAV audio", 502)
    if number != "default" and (
        headers.get("X-Jarvis-Voice-Variant") != number
        or headers.get("X-Jarvis-Voice-Status") != "selected"
    ):
        raise VoiceManagerError("Worker used fallback; preview blocked", 409)
    return audio
