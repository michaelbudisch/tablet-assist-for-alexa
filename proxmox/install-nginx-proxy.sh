#!/usr/bin/env bash
# Run inside a NEW dedicated Debian CT. No router/firewall changes.
set -Eeuo pipefail
[[ $EUID -eq 0 && -r /etc/debian_version && -d /run/systemd/system ]] || { echo "Run as root in a Debian systemd guest."; exit 1; }
if command -v pveversion >/dev/null; then echo "Refusing to install on the Proxmox host."; exit 1; fi
[[ $# -eq 3 ]] || { echo "Usage: $0 {prepare|enable} PUBLIC_HOST SPEECHSERVER_HOST"; exit 2; }
MODE=$1; HOST=$2; UPSTREAM=$3
[[ "$MODE" == prepare || "$MODE" == enable ]] || exit 2
DIR=$(cd "$(dirname "$0")" && pwd)
SITE=/etc/nginx/sites-available/tablet-assist-audio
LINK=/etc/nginx/sites-enabled/tablet-assist-audio
MARK='# Managed by tablet-assist-for-alexa; dedicated proxy only.'
TMP=$(mktemp)
BACKUP=$(mktemp)
trap 'rm -f "$TMP" "$BACKUP"' EXIT
if [[ "$MODE" == enable ]]; then
    python3 "$DIR/render-nginx-proxy.py" "$HOST" "$UPSTREAM" --tls > "$TMP"
    [[ -r "/etc/letsencrypt/live/$HOST/fullchain.pem" && -r "/etc/letsencrypt/live/$HOST/privkey.pem" ]] || { echo "A trusted certificate is required. Follow docs/nginx-proxy.md."; exit 1; }
    [[ -f "$SITE" && ! -L "$SITE" && $(head -n 1 "$SITE") == "$MARK" && -L "$LINK" && $(readlink "$LINK") == "$SITE" ]] || { echo "Run prepare first."; exit 1; }
else
    if ! command -v python3 >/dev/null; then apt-get update && apt-get install -y python3; fi
    python3 "$DIR/render-nginx-proxy.py" "$HOST" "$UPSTREAM" > "$TMP"
    [[ ! -e "$SITE" && ! -e "$LINK" && ! -L "$LINK" ]] || { echo "Proxy already prepared; refusing to overwrite."; exit 1; }
    if [[ -d /etc/nginx/sites-enabled ]]; then
        for x in /etc/nginx/sites-enabled/*; do
            [[ ! -e "$x" || "$x" == /etc/nginx/sites-enabled/default ]] || { echo "Existing nginx site detected. Use a clean guest or manual config."; exit 1; }
        done
    fi
    apt-get update
    apt-get install -y nginx certbot curl ca-certificates
    install -d -m 0755 /var/lib/tablet-assist-acme/.well-known/acme-challenge
fi
HAD_SITE=0
if [[ -f "$SITE" ]]; then cp -p "$SITE" "$BACKUP"; HAD_SITE=1; fi
install -m 0644 "$TMP" "$SITE"
if [[ "$MODE" == prepare ]]; then ln -s "$SITE" "$LINK"; fi
DEFAULT=/etc/nginx/sites-enabled/default
RESTORE_DEFAULT=0
if [[ "$MODE" == prepare && -L "$DEFAULT" && $(readlink "$DEFAULT") == /etc/nginx/sites-available/default ]]; then
    rm "$DEFAULT"; RESTORE_DEFAULT=1
fi
rollback() {
    if (( HAD_SITE )); then install -m 0644 "$BACKUP" "$SITE"; else rm -f "$SITE" "$LINK"; fi
    if (( RESTORE_DEFAULT )); then ln -s /etc/nginx/sites-available/default "$DEFAULT"; fi
    nginx -t && systemctl reload nginx || true
}
if ! nginx -t || ! systemctl enable --now nginx || ! systemctl reload nginx; then
    rollback
    echo "Proxy config failed; previous site restored." >&2
    exit 1
fi
if [[ "$MODE" == prepare ]]; then
    echo "HTTP ACME route ready; audio is not yet publicly available."
    echo "Set public DNS and intended port routing, then run:"
    printf 'certbot certonly --webroot -w /var/lib/tablet-assist-acme -d %q\n' "$HOST"
    printf 'bash %q enable %q %q\n' "$0" "$HOST" "$UPSTREAM"
else
    install -d -m 0755 /etc/letsencrypt/renewal-hooks/deploy
    HOOK=/etc/letsencrypt/renewal-hooks/deploy/tablet-assist-nginx
    if [[ ! -e "$HOOK" ]]; then
        cat > "$HOOK" <<'EOF'
#!/bin/sh
nginx -t && systemctl reload nginx
EOF
        chmod 0755 "$HOOK"
    fi
    systemctl enable --now certbot.timer
    printf 'HTTPS proxy ready: https://%s (only temporary MP3 URLs).\n' "$HOST"
    echo "Verify externally using a non-confidential generated test MP3, then configure Home Assistant."
fi
