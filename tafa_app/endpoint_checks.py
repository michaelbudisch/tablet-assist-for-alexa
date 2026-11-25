"""Read-only, bounded private-LAN endpoint diagnostics and last STT routing.

No audio, prompts, transcripts or model requests; no public URL probing.
A listening TCP socket means reachable, not proof the GPU decoded speech.
"""
import ipaddress
import json
import socket
from urllib.parse import urlsplit

from speech_source import private_http_origin


def suggested_gpu_stt_host(gpu_base):
    """Offer the GPU Qwen LAN host when Whisper likely runs on the same machine."""
    if not gpu_base:
        return ""
    try:
        url = private_http_origin(gpu_base)
        host = urlsplit(url).hostname or ""
        # Do not infer opaque hostnames or domains; only a known private IPv4.
        ip = ipaddress.ip_address(host)
        return str(ip) if ip.version == 4 and ip.is_private else ""
    except (ValueError, TypeError):
        return ""


def probe_gpu_whisper(host, timeout=0.8):
    """Test configured Wyoming TCP:10300, without speaking or scanning hosts."""
    if not host:
        return "missing"
    try:
        # Enforce private RFC1918 or .local only, consistent with TAFA LAN URLs.
        private_http_origin("http://" + host + ":10300")
    except (ValueError, TypeError):
        return "invalid"
    try:
        with socket.create_connection((host, 10300), timeout=timeout):
            return "reachable"
    except (OSError, TimeoutError):
        return "offline"


def assess_endpoints(options, mode, runtime, links, wyoming_entries):
    """Summarize only configured service endpoints and registered STT IDs."""
    known = {item.get("id") for item in wyoming_entries}
    cpu_id = options.get("cpu_stt") or ""
    gpu_id = options.get("gpu_stt") or ""
    gpu_host = options.get("gpu_stt_host") or ""
    return {
        "external_piper_base": ("unused" if mode == "local" else
                                 "reachable" if runtime.get("piper_ready") is True else "offline"),
        "gpu_base": links.get("gpu", "missing"),
        "gpu_stt_host": probe_gpu_whisper(gpu_host),
        "mp3_base": links.get("mp3", "missing"),
        "public_audio_base": "configured_unchecked" if options.get("public_audio_base") else "missing",
        "cpu_stt": "selected" if cpu_id and cpu_id in known else "unverified" if cpu_id else "missing",
        "gpu_stt": "selected" if gpu_id and gpu_id in known else "unverified" if gpu_id else "missing",
        "llm_agent": "configured_unchecked" if options.get("llm_agent") else "missing",
    }


def recent_stt_backend(token):
    """Read the last HA STT-router backend, never infer GPU use from TCP alone."""
    if not token:
        return None
    try:
        from websockets.sync.client import connect
        with connect("ws://supervisor/core/websocket", open_timeout=2, close_timeout=2) as ws:
            hello = json.loads(ws.recv(timeout=3))
            if hello.get("type") == "auth_required":
                ws.send(json.dumps({"type": "auth", "access_token": token}))
                hello = json.loads(ws.recv(timeout=3))
            if hello.get("type") != "auth_ok":
                return None

            def query(identifier, command):
                ws.send(json.dumps({"id": identifier, "type": command}))
                for _ in range(8):
                    answer = json.loads(ws.recv(timeout=3))
                    if answer.get("id") == identifier:
                        return answer.get("result") if answer.get("success") else None
                return None

            registered = query(1, "config/entity_registry/list")
            if not isinstance(registered, list):
                return None
            routes = [
                item.get("entity_id")
                for item in registered
                if isinstance(item, dict)
                and item.get("platform") == "tablet_assist_for_alexa"
                and str(item.get("unique_id") or "").endswith("_stt_router")
                and str(item.get("entity_id") or "").startswith("stt.")
            ]
            if len(routes) != 1:
                return None
            states = query(2, "get_states")
            if not isinstance(states, list):
                return None
            entry = next((row for row in states if row.get("entity_id") == routes[0]), None)
            if not entry:
                return None
            attrs = entry.get("attributes") or {}
            backend = attrs.get("letztes_backend")
            if backend not in ("zusatzrechner", "homeserver"):
                return None
            duration = attrs.get("letzte_dauer_ms")
            if not isinstance(duration, (int, float)) or isinstance(duration, bool):
                duration = None
            return {"backend": backend, "duration_ms": duration}
    except (OSError, TimeoutError, ValueError, TypeError, KeyError):
        return None
