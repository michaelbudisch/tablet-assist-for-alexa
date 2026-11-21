#!/usr/bin/env bash
# Run inside a Debian proxy guest. Default: dedicated CT. Explicit --shared: add only a new audio hostname; never adopt an existing site.
set -Eeuo pipefail
[[ $EUID -eq 0 && -r /etc/debian_version && -d /run/systemd/system ]] || { echo "Run as root in a Debian systemd guest."; exit 1; }
if command -v pveversion >/dev/null; then echo "Refusing to install on the Proxmox host."; exit 1; fi
[[ $# -eq 3 || $# -eq 4 ]] || { echo "Usage: $0 {prepare|enable} PUBLIC_HOST SPEECHSERVER_HOST [--shared]"; exit 2; }
SHARED=0
if [[ $# -eq 4 ]]; then
    [[ "$4" == --shared ]] || exit 2
    SHARED=1
fi
MODE=$1; HOST=$2; UPSTREAM=$3
[[ "$MODE" == prepare || "$MODE" == enable ]] || exit 2
DIR=$(cd "$(dirname "$0")" && pwd)
SITE=/etc/nginx/sites-available/tablet-assist-audio
LINK=/etc/nginx/sites-enabled/tablet-assist-audio
MARK='# Managed by tablet-assist-for-alexa; dedicated proxy only.'
# The marker is retained for compatibility with 0.2.0 generated sites.
TMP=$(mktemp)
BACKUP=$(mktemp)
trap 'rm -f "$TMP" "$BACKUP"' EXIT
if [[ "$MODE" == enable ]]; then
    python3 "$DIR/render-nginx-proxy.py" "$HOST" "$UPSTREAM" --tls > "$TMP"
    [[ -r "/etc/letsencrypt/live/$HOST/fullchain.pem" && -r "/etc/letsencrypt/live/$HOST/privkey.pem" ]] || { echo "A trusted certificate is required. Follow docs/nginx-proxy.md."; exit 1; }
    [[ -f "$SITE" && ! -L "$SITE" && $(head -n 1 "$SITE") == "$MARK" && -L "$LINK" && $(readlink "$LINK") == "$SITE" ]] || { echo "Run prepare first."; exit 1; }
    grep -Fqx "    server_name $HOST;" "$SITE" || { echo "Hostname differs from prepared site; refusing to overwrite."; exit 1; }
else
    if ! command -v python3 >/dev/null; then apt-get update && apt-get install -y python3; fi
    python3 "$DIR/render-nginx-proxy.py" "$HOST" "$UPSTREAM" > "$TMP"
    [[ ! -e "$SITE" && ! -e "$LINK" && ! -L "$LINK" ]] || { echo "Proxy already prepared; refusing to overwrite."; exit 1; }
    if (( SHARED )); then
        command -v nginx >/dev/null && command -v certbot >/dev/null || { echo "Shared mode requires an existing Nginx/Certbot installation."; exit 1; }
        systemctl is-active --quiet nginx || { echo "Shared mode requires a running Nginx."; exit 1; }
        [[ -d /etc/nginx/sites-available && -d /etc/nginx/sites-enabled ]] || { echo "Expected Debian sites layout."; exit 1; }
        # Refuse exact hostname conflicts anywhere in the loaded config. Check wildcard/regex sites manually.
        nginx -T > "$BACKUP" 2>&1 || { echo "Existing nginx configuration does not pass validation."; exit 1; }
        python3 "$DIR/check-proxy-host.py" "$HOST" "$BACKUP"
        echo "Review wildcard/regex virtual hosts before proceeding; existing sites will not be edited."
    elif [[ -d /etc/nginx/sites-enabled ]]; then
        for x in /etc/nginx/sites-enabled/*; do
            [[ ! -e "$x" || "$x" == /etc/nginx/sites-enabled/default ]] || { echo "Existing nginx site detected. Use a clean guest or manual config."; exit 1; }
        done
    fi
    if (( ! SHARED )); then
        apt-get update
        apt-get install -y nginx certbot curl ca-certificates
    fi
    install -d -m 0755 /var/lib/tablet-assist-acme/.well-known/acme-challenge
fi
HAD_SITE=0
if [[ -f "$SITE" ]]; then cp -p "$SITE" "$BACKUP"; HAD_SITE=1; fi
install -m 0644 "$TMP" "$SITE"
if [[ "$MODE" == prepare ]]; then ln -s "$SITE" "$LINK"; fi
DEFAULT=/etc/nginx/sites-enabled/default
RESTORE_DEFAULT=0
if [[ "$MODE" == prepare && "$SHARED" == 0 && -L "$DEFAULT" && $(readlink "$DEFAULT") == /etc/nginx/sites-available/default ]]; then
    rm "$DEFAULT"; RESTORE_DEFAULT=1
fi
rollback() {
    if (( HAD_SITE )); then install -m 0644 "$BACKUP" "$SITE"; else rm -f "$SITE" "$LINK"; fi
    if (( RESTORE_DEFAULT )); then ln -s /etc/nginx/sites-available/default "$DEFAULT"; fi
    nginx -t && systemctl reload nginx || true
}
check_nginx() {
    local result
    result=$(nginx -t 2>&1) || { printf '%s\n' "$result" >&2; return 1; }
    printf '%s\n' "$result"
    # A duplicate name can otherwise be ignored with exit status 0.
    if grep -Fi "conflicting server name \"$HOST\"" <<< "$result" >/dev/null; then return 1; fi
    return 0
}
if ! check_nginx || { (( ! SHARED )) && ! systemctl enable --now nginx; } || ! systemctl reload nginx; then
    rollback
    echo "Proxy config failed; previous site restored." >&2
    exit 1
fi
if [[ "$MODE" == prepare ]]; then
    echo "HTTP ACME route ready; audio is not yet publicly available."
    echo "Set public DNS and intended port routing, then run:"
    printf 'certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %q -d %q\n' "$HOST" "$HOST"
    printf 'bash %q enable %q %q' "$0" "$HOST" "$UPSTREAM"
    if (( SHARED )); then printf ' --shared'; fi
    printf '\n'
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
    if (( ! SHARED )); then
        systemctl enable --now certbot.timer
    else
        echo "Existing Certbot scheduling unchanged; verify renewal is scheduled."
    fi
    printf 'HTTPS proxy ready: https://%s (only temporary MP3 URLs).\n' "$HOST"
    echo "Verify externally using a non-confidential generated test MP3, then configure Home Assistant."
fi
