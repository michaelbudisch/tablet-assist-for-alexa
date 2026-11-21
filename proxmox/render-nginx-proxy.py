#!/usr/bin/env python3
"""Generate a restricted nginx virtual host for a dedicated Debian proxy."""
import argparse
import re

def validate(host, upstream):
    label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    if len(host) > 253 or not re.fullmatch(label + r"(?:\." + label + r")+", host):
        raise ValueError("Specify a public DNS hostname without scheme, port or path")
    if len(upstream) > 253 or not re.fullmatch(label + r"(?:\." + label + r")*", upstream):
        raise ValueError("Specify an internal speechserver IPv4 address or DNS hostname")

def render(host, upstream, tls=False):
    validate(host, upstream)
    config = """# Managed by tablet-assist-for-alexa; dedicated proxy only.
server {
    listen 80;
    listen [::]:80;
    server_name @PUBLIC@;
    access_log off;
    location ^~ /.well-known/acme-challenge/ {
        root /var/lib/tablet-assist-acme;
        try_files $uri =404;
    }
    location / { return 404; }
}
""".replace("@PUBLIC@",host)
    if tls:
        config += r"""
limit_req_zone $binary_remote_addr zone=tablet_assist_audio:10m rate=10r/s;
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name @PUBLIC@;
    ssl_certificate /etc/letsencrypt/live/@PUBLIC@/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/@PUBLIC@/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    server_tokens off;
    access_log off;
    error_log /var/log/nginx/tablet-assist-error.log crit;
    if ($host != @PUBLIC@) { return 421; }
    location ~ "^/[a-f0-9]{32}\.mp3$" {
        limit_except GET { deny all; }
        if ($args != "") { return 404; }
        limit_req zone=tablet_assist_audio burst=30 nodelay;
        proxy_connect_timeout 3s;
        proxy_read_timeout 15s;
        proxy_pass http://@UPSTREAM@:8080;
        proxy_set_header Host $proxy_host;
        proxy_set_header Connection "";
        proxy_set_header Cookie "";
        proxy_set_header Authorization "";
        proxy_hide_header Cache-Control;
        add_header Cache-Control "no-store" always;
        proxy_hide_header X-Content-Type-Options;
        add_header X-Content-Type-Options nosniff always;
        proxy_cache off;
        proxy_redirect off;
    }
    location / { return 404; }
}
""".replace("@PUBLIC@",host).replace("@UPSTREAM@",upstream)
    return config

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hostname")
    parser.add_argument("upstream")
    parser.add_argument("--tls", action="store_true")
    args = parser.parse_args()
    try:
        print(render(args.hostname, args.upstream, args.tls))
    except ValueError as exc:
        parser.error(str(exc))
