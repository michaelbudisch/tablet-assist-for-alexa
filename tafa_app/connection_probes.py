"""Bounded, read-only connection diagnostics for manually entered TAFA origins.

No authentication, no redirects, no outbound probes to private addresses
discovered through public DNS, no requests with prompts or any credentials.
A TLS handshake is *not* proof that Alexa can fetch a public audio file.
"""
import http.client
import ipaddress
import re
import socket
import ssl
from urllib.parse import urlsplit

from speech_source import private_http_origin, setup_settings_values

ADDRESS_FIELDS = frozenset(("external_piper_base", "gpu_base",
                            "gpu_stt_host", "mp3_base", "public_audio_base"))
PRIVATE_NETWORKS = tuple(ipaddress.ip_network(n) for n in
                         ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))


def _private_address(ip):
    try:
        addr = ipaddress.ip_address(ip)
        return addr.version == 4 and any(addr in network for network in PRIVATE_NETWORKS)
    except ValueError:
        return False


def _resolve(host, port, *, public):
    addresses = socket.getaddrinfo(host, port, family=socket.AF_UNSPEC,
                                   type=socket.SOCK_STREAM)
    if not 0 < len(addresses) <= 16:
        raise ValueError("Unusable address")
    ips = [row[4][0] for row in addresses]
    if public:
        if not all(ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError("Public HTTPS host must resolve only to public IPs")
    elif not all(_private_address(ip) for ip in ips):
        raise ValueError("Local service resolves outside private RFC1918 LAN")
    return ips


def _probe_private(value, field):
    origin = private_http_origin(value)
    parsed = urlsplit(origin)
    ip = _resolve(parsed.hostname, parsed.port, public=False)[0]
    # Force direct validated IP, not a DNS lookup after the check.
    conn = http.client.HTTPConnection(ip, parsed.port, timeout=1.5)
    try:
        conn.request("GET", "/health", headers={
            "Host": parsed.hostname, "Accept": "application/json",
            "Connection": "close"})
        response = conn.getresponse()
        # A successful /health endpoint proves more than a listening socket.
        if response.status == 200:
            import json
            try:
                data = json.loads(response.read(2048))
            except (ValueError, UnicodeError):
                return {"status": "reachable", "detail": "http_200"}
            if isinstance(data, dict):
                if field == "mp3_base":
                    ready = data.get("status") == "online"
                else:
                    ready = data.get("ready") is True
                return {"status": "ready" if ready else "not_ready",
                        "detail": "health"}
            return {"status": "reachable", "detail": "http_200"}
        if response.status in (401, 403):
            return {"status": "reachable", "detail": "access_restricted"}
        return {"status": "reachable", "detail": "http_other"}
    except (OSError, TimeoutError, http.client.HTTPException):
        return {"status": "offline", "detail": "no_response"}
    finally:
        conn.close()


def _probe_whisper(value):
    # Valid host-only field and fixed Wyoming port; no arbitrary port scan.
    if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", value):
        raise ValueError("Invalid Wyoming host")
    private_http_origin("http://" + value + ":10300")
    ip = _resolve(value, 10300, public=False)[0]
    try:
        with socket.create_connection((ip, 10300), timeout=1.5):
            return {"status": "reachable", "detail": "tcp_only"}
    except (OSError, TimeoutError):
        return {"status": "offline", "detail": "no_response"}


def _probe_public_https(value):
    # Match the saved origin policy, additionally restrict live checks to
    # normal HTTPS/443: no arbitrary public port scanning, no URL paths.
    setup_settings_values({"public_audio_base": value})
    parsed = urlsplit(value.strip().rstrip("/"))
    host = parsed.hostname or ""
    # Public audio checks accept domain names only, never literal IPs.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("Public HTTPS requires a domain")
    if (not re.fullmatch(r"[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})+", host)
            or parsed.port not in (None, 443)
            or len(value) > 256):
        raise ValueError("Enter a public domain using HTTPS port 443")
    # Require DNS to resolve only to global addresses. No public IP literals.
    ip = _resolve(host, 443, public=True)[0]
    try:
        with socket.create_connection((ip, 443), timeout=1.5) as raw:
            raw.settimeout(1.5)
            with ssl.create_default_context().wrap_socket(raw, server_hostname=host):
                return {"status": "tls_ok", "detail": "tls_only"}
    except ssl.SSLError:
        return {"status": "tls_failed", "detail": "certificate"}
    except (OSError, TimeoutError):
        return {"status": "offline", "detail": "no_response"}


def probe_connection(field, value):
    """Sanitized states for the UI; never echo URLs, IPs or exception text."""
    if field not in ADDRESS_FIELDS or not isinstance(value, str) or len(value) > 256:
        return {"status": "invalid", "detail": "invalid_input"}
    value = value.strip()
    if not value:
        return {"status": "missing", "detail": "empty"}
    try:
        if field == "gpu_stt_host":
            return _probe_whisper(value)
        if field == "public_audio_base":
            return _probe_public_https(value)
        return _probe_private(value, field)
    except (ValueError, TypeError, OverflowError):
        return {"status": "invalid", "detail": "invalid_input"}
    except (OSError, socket.gaierror, TimeoutError):
        return {"status": "offline", "detail": "no_response"}
