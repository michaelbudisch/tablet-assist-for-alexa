#!/usr/bin/env python3
"""Check a local nginx -T dump before adding a new vhost. Never upload the dump."""
import re
import sys

def conflicts(host, config):
    # Strip comments on ordinary nginx config lines; check exact tokens, case-insensitively.
    clean = re.sub(r"(?m)#.*$", "", config)
    for names in re.findall(r"\bserver_name\s+([^;{}]+);", clean):
        for name in names.split():
            if name.strip("\"'").rstrip(".").lower() == host.rstrip(".").lower():
                return True
    return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: check-proxy-host.py HOST NGINX_CONFIG_DUMP")
    with open(sys.argv[2], encoding="utf-8", errors="replace") as stream:
        if conflicts(sys.argv[1], stream.read()):
            raise SystemExit("Hostname already exists in nginx. Preserve the site; use manual configuration review.")
