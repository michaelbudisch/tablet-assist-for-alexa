#!/usr/bin/env python3
"""Update one *existing* DuckDNS IPv4 A record, never create domains.

The DuckDNS token is read from a root-only local JSON file, not command-line
arguments or systemd unit text. Never log URL, token or response bodies.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CONFIG_DIR = Path("/etc/tafa-duckdns")


def update(config_path):
    path = Path(config_path)
    if not path.is_file() or path.is_symlink() or CONFIG_DIR not in path.parents:
        raise ValueError("Use a regular TAFA DuckDNS configuration file")
    if path.stat().st_mode & 0o077:
        raise ValueError("DuckDNS config is not private (expected 0600)")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or set(obj) != {"domain", "token"}:
        raise ValueError("Unexpected DuckDNS config format")
    domain = obj["domain"]
    token = obj["token"]
    if not isinstance(domain, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,61}\.duckdns\.org", domain):
        raise ValueError("Invalid DuckDNS hostname")
    if not isinstance(token, str) or not re.fullmatch(r"[0-9A-Za-z_-]{16,128}", token):
        raise ValueError("Invalid DuckDNS token")
    # DuckDNS documents the update endpoint for REGISTERED domains. No
    # credentials are stored in public scripts or home assistant config.
    qs = urlencode({"domains": domain.removesuffix(".duckdns.org"), "token": token, "ip": ""})
    request = Request("https://www.duckdns.org/update?" + qs, headers={"User-Agent": "TAFA-DuckDNS/1"})
    with urlopen(request, timeout=20) as response:
        status = response.read(16).decode("ascii", errors="ignore").strip()
    if status != "OK":
        raise RuntimeError("DuckDNS refused the update (check registration and token)")
    return domain


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: duckdns-update.py CONFIG_FILE", file=sys.stderr)
        raise SystemExit(2)
    try:
        domain = update(sys.argv[1])
        print("DuckDNS IPv4 updated:", domain)
    except Exception as exc:
        # Never leak an exception containing URLs or token query parameters.
        print("DuckDNS update failed; check DNS, account registration and local settings.", file=sys.stderr)
        raise SystemExit(1) from None
