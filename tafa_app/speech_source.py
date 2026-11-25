"""Read supervised App options and probe only explicitly selected private LAN services.

No token fields, discovery, redirect following, environment proxies or public
GPU/MP3 endpoints. The TAFA Control Center and the advanced HA App editor use the same Supervisor options.
"""
import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler, Request

OPTIONS_FILE = Path("/data/options.json")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


HTTP = build_opener(ProxyHandler({}), _NoRedirect())


def load_options(path=OPTIONS_FILE):
    try:
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError) as exc:
        raise ValueError("Cannot read TAFA App options") from exc
    if not isinstance(value, dict):
        raise ValueError("Invalid TAFA App options")
    return value


def private_http_origin(value):
    """Accept explicit RFC1918 IPv4 or .local hostname with a required HTTP port."""
    if not isinstance(value, str):
        raise ValueError("Private service URL must be a string")
    base = value.strip().rstrip("/")
    parsed = urlsplit(base)
    if (parsed.scheme != "http" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("Expected private LAN HTTP origin with no path or credentials")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid private service port") from exc
    if port is None or not 1 <= port <= 65535:
        raise ValueError("Private service URL requires a port")
    host = parsed.hostname.lower()
    try:
        ip = ipaddress.ip_address(host)
        allowed = ip.version == 4 and any(
            ip in ipaddress.ip_network(network) for network in
            ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
        )
    except ValueError:
        allowed = (
            host.endswith(".local") and 0 < len(host) <= 253 and
            all(label and label[0].isalnum() and label[-1].isalnum() and
                re.fullmatch(r"[a-z0-9-]+", label) for label in host.split("."))
        )
    if not allowed:
        raise ValueError("Service must be in a trusted private IPv4 LAN or .local")
    return base


def choose(path=OPTIONS_FILE):
    """Return setup/local/external without waking bundled models in setup mode."""
    values = load_options(path)
    mode = values.get("speech_mode", "local")
    if mode not in ("setup", "local", "external"):
        raise ValueError("Choose setup, local or external speech mode")
    if mode in ("setup", "local"):
        return mode, ""
    return "external", private_http_origin(values.get("external_piper_base", ""))



# Match the public HA integration's source names and expected entity domains.
SOURCE_DOMAINS = {
    "weather": "weather", "shopping": "todo",
    **dict.fromkeys(("restmuell", "bioabfall", "papier", "wertstoff",
       "vorlauf", "ruecklauf", "spreizung", "preis", "guenstig", "netz",
       "solar", "prognose", "solarheute", "netzheute", "einspeisungheute",
       "heizoel", "oelverbrauch", "waschmaschine", "waschkosten",
       "waschenergie", "waermepumpe", "wpheute", "wpkosten",
       "kuehlschrank", "kuehlschrankheute"), "sensor"),
}
ROOMS = {"Büro", "Wohnzimmer", "Badezimmer", "Schlafzimmer", "Kinderzimmer"}


def _entity(value, domain):
    if not isinstance(value, str) or (
        value and not re.fullmatch(domain + r"\.[a-z0-9_]+", value)
    ):
        raise ValueError("Invalid " + domain + " entity ID")
    return value


def _mapping(value, label):
    if not isinstance(value, str):
        raise ValueError(label + " must be JSON text")
    try:
        result = json.loads(value or "{}")
    except (ValueError, TypeError) as exc:
        raise ValueError(label + " contains invalid JSON") from exc
    if not isinstance(result, dict):
        raise ValueError(label + " must contain an object")
    return result


def _advanced(values):
    rooms = _mapping(values.get("rooms_json", "{}"), "rooms_json")
    if len(rooms) > len(ROOMS) or any(k not in ROOMS for k in rooms):
        raise ValueError("Unrecognized Alexa room")
    for room in rooms.values():
        if not isinstance(room, dict) or set(room) - {"notify", "dnd", "quiet"} or not room.get("notify"):
            raise ValueError("Invalid Alexa room mapping")
        for key, domain in (("notify", "notify"), ("dnd", "switch"), ("quiet", "schedule")):
            if key in room:
                _entity(room[key], domain)
    sources = _mapping(values.get("sources_json", "{}"), "sources_json")
    if set(sources) - set(SOURCE_DOMAINS):
        raise ValueError("Unknown HA data source")
    for key, value in sources.items():
        _entity(value, SOURCE_DOMAINS[key])
    result = {"rooms_json": json.dumps(rooms, ensure_ascii=False),
              "sources_json": json.dumps(sources, ensure_ascii=False)}
    for key, domain in (("cpu_stt", "stt"), ("gpu_stt", "stt"),
                        ("llm_agent", "conversation")):
        result[key] = _entity(values.get(key, "") or "", domain)
    if result["cpu_stt"] and result["gpu_stt"] == result["cpu_stt"]:
        raise ValueError("CPU and GPU Wyoming entities must differ")
    host = values.get("gpu_stt_host", "") or ""
    if not isinstance(host, str) or (host and not re.fullmatch(r"[A-Za-z0-9.-]+", host)):
        raise ValueError("Invalid GPU Whisper host")
    result["gpu_stt_host"] = host
    cmode = values.get("conversation_mode", "intelligent")
    if cmode not in ("manual", "automatic", "intelligent"):
        raise ValueError("Invalid conversation mode")
    result["conversation_mode"] = cmode
    for key in ("reminders_enabled", "learning_enabled"):
        result[key] = values.get(key, False)
        if not isinstance(result[key], bool):
            raise ValueError("Expected Boolean for " + key)
    room = values.get("reminder_room", "") or ""
    if not isinstance(room, str) or (room and room not in rooms):
        raise ValueError("Reminder room must be configured among Alexa rooms")
    result["reminder_room"] = room
    return result

def setup_settings(path=OPTIONS_FILE):
    """Read and validate stored options."""
    return setup_settings_values(load_options(path))


def setup_settings_values(values):
    """Validate proposed options before persisting them."""
    gpu = values.get("gpu_base", "") or ""
    mp3 = values.get("mp3_base", "") or ""
    public = values.get("public_audio_base", "") or ""
    if not all(isinstance(item, str) for item in (gpu, mp3, public)):
        raise ValueError("Service URLs must be strings")
    if public:
        public = public.strip().rstrip("/")
        parsed = urlsplit(public)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                parsed.path or parsed.query or parsed.fragment or
                not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?", public)):
            raise ValueError("Public Alexa audio origin must be HTTPS without a path")
        try:
            if parsed.port is not None and not 1 <= parsed.port <= 65535:
                raise ValueError("Invalid public audio port")
        except ValueError as exc:
            raise ValueError("Invalid public audio port") from exc
    mode = values.get("hardware_profile", "automatic")
    if mode not in ("automatic", "cpu"):
        raise ValueError("Invalid routing mode")
    variant = values.get("voice_variant", "default")
    if variant not in ("default", *map(str, range(1, 10))):
        raise ValueError("Invalid voice variant")
    live = values.get("live_profile", "natural")
    if live not in ("natural", "studio", "clear"):
        raise ValueError("Invalid sound profile")
    mp3_profile = values.get("mp3_profile", "natural")
    if mp3_profile not in ("natural", "studio", "announcement"):
        raise ValueError("Invalid MP3 profile")
    if not isinstance(values.get("chime", False), bool):
        raise ValueError("Chime must be a boolean")
    advanced = _advanced(values)
    if advanced["rooms_json"] != "{}" and not (mp3 and public):
        raise ValueError("Alexa rooms require MP3 generator and HTTPS audio")
    return {
        **advanced,
        "gpu_base": private_http_origin(gpu) if gpu else "",
        "hardware_profile": mode,
        "voice_variant": variant,
        "live_profile": live,
        "mp3_base": private_http_origin(mp3) if mp3 else "",
        "public_audio_base": public,
        "mp3_profile": mp3_profile,
        "chime": values.get("chime", False),
    }


def read_health(base, timeout=2):
    """Return a bounded JSON health response, or None if unreachable/invalid."""
    try:
        with HTTP.open(Request(base + "/health", method="GET"), timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read(65536))
            return data if isinstance(data, dict) else None
    except (OSError, ValueError, TimeoutError):
        return None


def piper_ready(base):
    """Local Proxmox Piper /health contract: {ready: true}."""
    data = read_health(base, timeout=3)
    return isinstance(data, dict) and data.get("ready") is True


def connection_status(settings, piper_online):
    """Read-only view of GPU, MP3 generator and the expected fallback route."""
    gpu_url = settings.get("gpu_base", "")
    gpu = read_health(gpu_url) if gpu_url else None
    if not gpu_url:
        gpu_state = "not_configured"
    elif gpu is None:
        gpu_state = "offline"
    elif gpu.get("busy"):
        gpu_state = "busy"
    elif gpu.get("ready") is True:
        gpu_state = "ready"
    else:
        gpu_state = "not_ready"
    mp3_url = settings.get("mp3_base", "")
    mp3 = read_health(mp3_url) if mp3_url else None
    if not mp3_url:
        mp3_state = "not_configured"
    elif isinstance(mp3, dict) and mp3.get("status") == "online":
        mp3_state = "ready"
    else:
        mp3_state = "offline"
    if settings.get("hardware_profile") == "cpu":
        selected = "piper" if piper_online else "none"
    elif gpu_state == "ready":
        selected = "qwen"
    else:
        selected = "piper" if piper_online else "none"
    return {
        "gpu": gpu_state,
        "gpu_version": str((gpu or {}).get("worker_version", ""))[:40],
        "mp3": mp3_state,
        "route": selected,
        "piper": "ready" if piper_online else "offline",
    }
