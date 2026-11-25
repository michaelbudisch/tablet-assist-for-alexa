"""Select local CPU speech or an explicitly configured trusted Proxmox service.

The selection is read from the Supervisor-managed /data/options.json.
No credentials, host discovery, network scanning or configuration mutation.
"""
import ipaddress
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler, Request

OPTIONS_FILE = Path("/data/options.json")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


HTTP = build_opener(ProxyHandler({}), _NoRedirect())


def choose(path=OPTIONS_FILE):
    """Return ('local', '') or ('external', validated Piper HTTP origin)."""
    try:
        values = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError) as exc:
        raise ValueError("Cannot read TAFA App options") from exc
    if not isinstance(values, dict):
        raise ValueError("Invalid TAFA App options")
    mode = values.get("speech_mode", "local")
    if mode not in ("local", "external"):
        raise ValueError("Choose local or external speech mode")
    if mode == "local":
        return mode, ""
    base = values.get("external_piper_base", "")
    if not isinstance(base, str):
        raise ValueError("External Piper URL must be text")
    base = base.strip().rstrip("/")
    parsed = urlsplit(base)
    if (parsed.scheme != "http" or not parsed.hostname or parsed.username or
            parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("External Piper URL must be http://PRIVATE-LAN-HOST:5000")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid external Piper port") from exc
    if port is None or not 1 <= port <= 65535:
        raise ValueError("External Piper URL requires a port")
    hostname = parsed.hostname.lower()
    try:
        ip = ipaddress.ip_address(hostname)
        allowed = ip.version == 4 and any(
            ip in ipaddress.ip_network(net) for net in
            ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
        )
    except ValueError:
        allowed = (hostname.endswith(".local") and len(hostname) <= 253 and
                   all(label and label.replace("-", "").isalnum()
                       for label in hostname.split(".")))
    if not allowed:
        raise ValueError("External speech host must be a trusted RFC1918 LAN IPv4 or .local hostname")
    return mode, base


def piper_ready(base):
    """Check external Piper without redirecting or using environment proxies."""
    try:
        with HTTP.open(Request(base + "/health", method="GET"), timeout=3) as response:
            if response.status != 200:
                return False
            data = json.loads(response.read(65536))
            return isinstance(data, dict) and data.get("ready") is True
    except (OSError, ValueError, TimeoutError):
        return False
