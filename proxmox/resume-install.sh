#!/usr/bin/env bash
# Continue a NEW TAFA CT interrupted at one of two verified points:
# (1) Debian CT created but no TAFA speech files installed, or
# (2) Python venv installed but service setup interrupted before voice download.
# This script never destroys CTs or modifies existing Nginx sites.
set -Eeuo pipefail
export LC_ALL=C
umask 077
[[ "$EUID" == 0 && -t 0 && -r /dev/tty ]] || {
  echo "Run as root in an interactive Proxmox VE host shell."; exit 1;
}
for cmd in pct pveversion curl tar python3 flock; do
  command -v "$cmd" >/dev/null || { echo "Missing PVE tool: $cmd"; exit 1; }
done
ask() {
  printf '%s%s: ' "$1" "$2" >/dev/tty
  IFS= read -r REPLY_VALUE </dev/tty
}
fail() { echo "ERROR: $*" >&2; exit 1; }
printf '\nTAFA | Continue an interrupted CT installation\n'
printf 'Supports a newly created, empty TAFA CT or an interrupted Python venv stage.\n'
printf 'Existing functional installations will not be overwritten.\n'
ask 'Interrupted speech CT ID (e.g. 110)' ''
CTID="$REPLY_VALUE"
[[ "$CTID" =~ ^[1-9][0-9]{2,7}$ ]] || fail "Invalid CT ID"
[[ "$(pct status "$CTID" 2>/dev/null)" == *running* ]] || fail "Container is not running"
CT_CONFIG="$(pct config "$CTID")" || fail "Could not inspect container configuration"
grep -qx 'ostype: debian' <<< "$CT_CONFIG" || fail "Recovery requires a Debian CT"
grep -qx 'unprivileged: 1' <<< "$CT_CONFIG" || fail "Recovery requires an unprivileged CT"
# An interrupted shell could leave a running installer attached to ANOTHER
# host console. Never run two installers against the same guest.
exec 9>"/run/lock/tafa-resume-$CTID.lock"
flock -n 9 || fail "Another TAFA recovery for this CT is active"
pct exec "$CTID" -- test ! -e /etc/jarvis-local.env || fail "Existing live TAFA configuration found; refusing to overwrite"
pct exec "$CTID" -- test ! -e /etc/tafa-combined-hostname || fail "TAFA CT is already configured"
pct exec "$CTID" -- test ! -e /usr/local/sbin/tafa-info || fail "TAFA console is already configured"
pct exec "$CTID" -- test ! -L /opt/jarvis-local || fail "Unexpected symlink in TAFA installation path"
pct exec "$CTID" -- test ! -L /opt/tafa-installer || fail "Unexpected symlink in installer directory"
if pct exec "$CTID" -- test ! -e /opt/jarvis-local; then
  STAGE=empty
  # No speech services, runtime configuration or any preexisting unknown
  # installer directory may be overwritten.
  for unit in jarvis-piper jarvis-whisper jarvis-mp3 jarvis-audio; do
    pct exec "$CTID" -- systemctl cat "$unit.service" >/dev/null 2>&1 &&
      fail "Unexpected existing $unit.service. Refusing empty-stage recovery."
  done
  if pct exec "$CTID" -- test -e /opt/tafa-installer; then
    pct exec "$CTID" -- test -f /opt/tafa-installer/proxmox/install-combined-ct.sh ||
      fail "Unknown installer files under /opt/tafa-installer"
  fi
elif pct exec "$CTID" -- test -d /opt/jarvis-local/venv &&
     pct exec "$CTID" -- test -f /opt/jarvis-local/requirements.txt &&
     pct exec "$CTID" -- test -f /opt/tafa-installer/proxmox/install-combined-ct.sh; then
  STAGE=venv
else
  fail "Unsupported partial-install stage. Inspect the CT manually; no changes made."
fi
CT_HOSTNAME="$(pct exec "$CTID" -- hostname -s)" || fail "Cannot read CT hostname"
printf 'Detected CT %s (%s), recovery stage: %s\n' "$CTID" "$CT_HOSTNAME" "$STAGE"
printf 'The original Proxmox CT and its root disk will be preserved.\n'
ask 'Registered new public audio hostname (without https://)' ''
HOST="$REPLY_VALUE"
python3 - "$HOST" <<'PY' || fail "Invalid public hostname"
import re,sys
v=sys.argv[1]
label=r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
assert len(v)<=253 and re.fullmatch(label+r"(?:\."+label+r")+",v) and not v.endswith(".local")
PY
ask 'Optional GPU worker URL (http://LAN-IP:10502; blank = Piper only)' ''
GPU="$REPLY_VALUE"
if [[ -n "$GPU" ]]; then
  python3 - "$GPU" <<'PY' || fail "Invalid GPU worker URL"
import ipaddress,sys
from urllib.parse import urlsplit
u=urlsplit(sys.argv[1])
assert u.scheme=="http" and u.hostname and u.port and not any((u.username,u.password,u.path,u.query,u.fragment))
ip=ipaddress.ip_address(u.hostname)
assert ip.version==4 and ip.is_private and not ip.is_loopback
PY
fi
ask 'HTTPS mode [shared]' ''
MODE="${REPLY_VALUE:-shared}"
[[ "$MODE" == shared ]] || fail "This recovery wizard only supports shared proxy mode"
ask 'Existing central Nginx proxy CT ID (required, no default)' ''
PROXY_CT="$REPLY_VALUE"
[[ "$PROXY_CT" =~ ^[1-9][0-9]{2,7}$ && "$PROXY_CT" != "$CTID" ]] || fail "Invalid proxy CT ID"
[[ "$(pct status "$PROXY_CT" 2>/dev/null)" == *running* ]] || fail "Proxy CT is not running"
pct exec "$PROXY_CT" -- nginx -t || fail "Proxy Nginx configuration failed validation"
pct exec "$PROXY_CT" -- bash -lc 'command -v certbot >/dev/null' || fail "Certbot is missing from the proxy CT"
pct exec "$PROXY_CT" -- test ! -e /etc/nginx/sites-available/tablet-assist-audio || fail "TAFA audio Nginx site already exists"
PROXY_IP="$(pct exec "$PROXY_CT" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
[[ -n "$PROXY_IP" ]] || fail "No private IPv4 address found for the proxy CT"
printf '\nContinue CT %s (%s), new public hostname %s, existing proxy CT %s (%s)\n' "$CTID" "$CT_HOSTNAME" "$HOST" "$PROXY_CT" "$PROXY_IP"
if [[ "$STAGE" == empty ]]; then
  printf 'TAFA has not been installed yet. Speech services will be installed in the existing CT.\n'
else
  printf 'Existing Python packages will be reused and their permissions repaired.\n'
fi
printf 'Only one NEW audio virtual host will be prepared on the existing proxy.\n'
ask 'To confirm, type RESUME' ''
[[ "$REPLY_VALUE" == RESUME ]] || fail "Cancelled without changes"

WORK="$(mktemp -d /tmp/tafa-resume.XXXXXXXX)"
trap 'rm -rf -- "$WORK"' EXIT
curl -fLSs --retry 2 --connect-timeout 15 --max-time 180 \
  https://github.com/michaelbudisch/tablet-assist-for-alexa/archive/refs/heads/main.tar.gz \
  -o "$WORK/repo.tar.gz"
tar -xzf "$WORK/repo.tar.gz" -C "$WORK"
SRC="$WORK/tablet-assist-for-alexa-main"
if [[ "$STAGE" == empty ]]; then
  # This mirrors the *post-pct-create* section of quick-install.sh.
  # No second CT is created and no existing speech files are overwritten.
  for file in speechserver/api.py speechserver/audio_server.py \
              proxmox/install-speechserver.sh proxmox/install-combined-ct.sh; do
    [[ -f "$SRC/$file" ]] || fail "Missing TAFA source file: $file"
  done
  tar -C "$SRC" -czf "$WORK/guest-installer.tar.gz" speechserver proxmox
  pct push "$CTID" "$WORK/guest-installer.tar.gz" /tmp/tafa-guest-installer.tar.gz
  pct exec "$CTID" -- mkdir -p /opt/tafa-installer
  pct exec "$CTID" -- tar -xzf /tmp/tafa-guest-installer.tar.gz -C /opt/tafa-installer
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh \
    "$HOST" "$GPU" shared "$PROXY_IP" "$PROXY_CT" "$CTID"
else
  # Do not reinstall pip requirements. Replace only TAFA-owned staged scripts.
  for file in install-speechserver.sh install-combined-ct.sh; do
    [[ -f "$SRC/proxmox/$file" ]] || fail "Missing new $file"
    pct push "$CTID" "$SRC/proxmox/$file" "/opt/tafa-installer/proxmox/$file"
  done
  pct push "$CTID" "$SRC/speechserver/audio_server.py" /opt/jarvis-local/audio_server.py
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh \
    --resume "$HOST" "$GPU" shared "$PROXY_IP" "$PROXY_CT" "$CTID"
fi
NEW_IP="$(pct exec "$CTID" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
[[ -n "$NEW_IP" ]] || fail "The new CT has no private IPv4 address"
SETUP="/opt/tafa-audio-setup-$CTID"
pct exec "$PROXY_CT" -- test ! -e "$SETUP" || fail "Proxy setup directory already exists"
pct exec "$PROXY_CT" -- mkdir -m 0700 "$SETUP"
for file in install-nginx-proxy.sh render-nginx-proxy.py check-proxy-host.py install-duckdns-updater.sh duckdns-update.py; do
  pct push "$PROXY_CT" "$SRC/proxmox/$file" "$SETUP/$file"
done
pct exec "$PROXY_CT" -- bash "$SETUP/install-nginx-proxy.sh" prepare "$HOST" "$NEW_IP" --shared

printf '\n=== TAFA speech installation resumed ===\n'
pct exec "$CTID" -- /usr/local/sbin/tafa-info || true
printf '\nNext, issue the TLS certificate inside proxy CT %s:\n' "$PROXY_CT"
printf '  pct enter %s\n' "$PROXY_CT"
printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$HOST" "$HOST"
printf '  bash %s/install-nginx-proxy.sh enable %s %s --shared\n' "$SETUP" "$HOST" "$NEW_IP"
printf 'Optional DuckDNS IPv4 updater:\n'
printf '  bash %s/install-duckdns-updater.sh %s\n' "$SETUP" "$HOST"
printf 'Existing TAFA services and Nginx sites are preserved.\n'
