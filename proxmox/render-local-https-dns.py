#!/usr/bin/env python3
"""Generate an optional split-DNS rule for an existing LAN HTTPS proxy."""
import argparse
from ipaddress import IPv4Address, IPv4Network
import re

LAN = tuple(IPv4Network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")

def valid_hostname(value):
    if not isinstance(value, str) or len(value) < 4 or len(value) > 253:
        raise ValueError("Expected a DNS hostname, not a URL or IP")
    name = value.rstrip(".").lower()
    if "." not in name or any(not LABEL.fullmatch(p) for p in name.split(".")):
        raise ValueError("Expected a DNS hostname, not a URL or IP")
    return name

def private_ip(value):
    try:
        addr = IPv4Address(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("Expected an RFC1918 private IPv4 address") from exc
    if not any(addr in subnet for subnet in LAN):
        raise ValueError("Expected an RFC1918 private IPv4 address")
    return str(addr)

def render(hostname, proxy_ip, upstream_ip):
    host = valid_hostname(hostname)
    proxy = private_ip(proxy_ip)
    upstream = private_ip(upstream_ip)
    if proxy == upstream:
        raise ValueError("Proxy and upstream DNS must have different IPs")
    return (
        "# Managed by TAFA optional local HTTPS DNS setup.\n"
        "bind-dynamic\n"
        f"listen-address={proxy}\n"
        "no-resolv\n"
        f"server={upstream}\n"
        "# Never forward this host's A or AAAA lookups to public DNS.\n"
        f"local=/{host}/\n"
        f"host-record={host},{proxy}\n"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hostname")
    parser.add_argument("proxy_ip")
    parser.add_argument("upstream_ip")
    args = parser.parse_args()
    try:
        print(render(args.hostname, args.proxy_ip, args.upstream_ip), end="")
    except ValueError as exc:
        parser.error(str(exc))
