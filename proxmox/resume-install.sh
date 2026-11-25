#!/usr/bin/env bash
# Recover ONLY a fresh TAFA combined CT interrupted immediately after pip install
# at "runuser: failed to execute .../venv/bin/python: Permission denied".
# This script never destroys CTs or modifies existing Nginx sites.
set -Eeuo pipefail
export LC_ALL=C
umask 077
[[ "$EUID" == 0 && -t 0 && -r /dev/tty ]] || {
  echo "Run as root in an interactive Proxmox VE host shell."; exit 1;
}
for cmd in pct pveversion curl tar python3; do
  command -v "$cmd" >/dev/null || { echo "Missing PVE tool: $cmd"; exit 1; }
done
ask() {
  printf '%s%s: ' "$1" "$2" >/dev/tty
  IFS= read -r REPLY_VALUE </dev/tty
}
fail() { echo "ERROR: $*" >&2; exit 1; }
printf '\nTAFA · Installationsfortsetzung nach Python-Berechtigungsfehler\n'
printf 'Es wird nur der unvollstaendige neue Sprachserver-CT repariert.\n'
ask 'ID des unterbrochenen Sprachserver-CT (z. B. 110)' ''
CTID="$REPLY_VALUE"
[[ "$CTID" =~ ^[1-9][0-9]{2,7}$ ]] || fail "Ungueltige CT-ID"
[[ "$(pct status "$CTID" 2>/dev/null)" == *running* ]] || fail "Container laeuft nicht"
pct exec "$CTID" -- test -d /opt/jarvis-local/venv || fail "Keine vorbereitete TAFA Python-Umgebung"
pct exec "$CTID" -- test -f /opt/jarvis-local/requirements.txt || fail "TAFA speechserver files fehlen"
pct exec "$CTID" -- test ! -e /etc/jarvis-local.env || fail "Installationsphase bereits vorbei; keinesfalls erneut reparieren"
pct exec "$CTID" -- test ! -e /etc/tafa-combined-hostname || fail "Bereits konfiguriert"
pct exec "$CTID" -- test -f /opt/tafa-installer/proxmox/install-combined-ct.sh || fail "Original-Installer fehlt"
ask 'Registrierter neuer Audio-DNS-Hostname (ohne https://)' ''
HOST="$REPLY_VALUE"
python3 - "$HOST" <<'PY' || fail "Hostname ungueltig"
import re,sys
v=sys.argv[1]
label=r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
assert len(v)<=253 and re.fullmatch(label+r"(?:\."+label+r")+",v) and not v.endswith(".local")
PY
ask 'Optionaler GPU-Worker (http://LAN-IP:10502; leer = Piper)' ''
GPU="$REPLY_VALUE"
if [[ -n "$GPU" ]]; then
  python3 - "$GPU" <<'PY' || fail "GPU-Adresse ungueltig"
import ipaddress,sys
from urllib.parse import urlsplit
u=urlsplit(sys.argv[1])
assert u.scheme=="http" and u.hostname and u.port and not any((u.username,u.password,u.path,u.query,u.fragment))
ip=ipaddress.ip_address(u.hostname)
assert ip.version==4 and ip.is_private and not ip.is_loopback
PY
fi
ask 'HTTPS-Modus [shared]' ''
MODE="${REPLY_VALUE:-shared}"
[[ "$MODE" == shared ]] || fail "Dieser Wiederaufnahme-Assistent unterstuetzt nur shared; bitte nichts ungeprueft aendern"
ask 'Bestehender Nginx-Proxy CT [101]' ''
PROXY_CT="${REPLY_VALUE:-101}"
[[ "$PROXY_CT" =~ ^[1-9][0-9]{2,7}$ && "$PROXY_CT" != "$CTID" ]] || fail "Ungueltiger Proxy-CT"
[[ "$(pct status "$PROXY_CT" 2>/dev/null)" == *running* ]] || fail "Proxy CT laeuft nicht"
pct exec "$PROXY_CT" -- nginx -t || fail "Proxy-Konfiguration ungueltig"
pct exec "$PROXY_CT" -- bash -lc 'command -v certbot >/dev/null' || fail "Proxy hat kein Certbot"
pct exec "$PROXY_CT" -- test ! -e /etc/nginx/sites-available/tablet-assist-audio || fail "TAFA Nginx-Audio-Site existiert schon"
PROXY_IP="$(pct exec "$PROXY_CT" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
[[ -n "$PROXY_IP" ]] || fail "Keine private IPv4 des Proxy-CT"
printf '\nFortsetzen: CT %s, neuer Host %s, gemeinsamer Proxy CT %s (%s)\n' "$CTID" "$HOST" "$PROXY_CT" "$PROXY_IP"
printf 'Die venv-Paketdateien werden lesbar gemacht. CT 101 erhaelt spaeter nur eine neue Audio-Site.\n'
ask 'Zur Bestaetigung FORTSETZEN eintippen' ''
[[ "$REPLY_VALUE" == FORTSETZEN ]] || fail "Abgebrochen, unveraendert"

WORK="$(mktemp -d /tmp/tafa-resume.XXXXXXXX)"
trap 'rm -rf -- "$WORK"' EXIT
curl -fLSs --retry 2 --connect-timeout 15 --max-time 180 \
  https://github.com/michaelbudisch/tablet-assist-for-alexa/archive/refs/heads/main.tar.gz \
  -o "$WORK/repo.tar.gz"
tar -xzf "$WORK/repo.tar.gz" -C "$WORK"
SRC="$WORK/tablet-assist-for-alexa-main"
for file in install-speechserver.sh install-combined-ct.sh; do
  [[ -f "$SRC/proxmox/$file" ]] || fail "Missing new $file"
  pct push "$CTID" "$SRC/proxmox/$file" "/opt/tafa-installer/proxmox/$file"
done
# Freshly updated audio file code also includes the shared-proxy IP allowlist.
pct push "$CTID" "$SRC/speechserver/audio_server.py" /opt/jarvis-local/audio_server.py

pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh \
  --resume "$HOST" "$GPU" shared "$PROXY_IP" "$PROXY_CT" "$CTID"
NEW_IP="$(pct exec "$CTID" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
[[ -n "$NEW_IP" ]] || fail "Keine private IPv4 am neuen CT"
SETUP="/opt/tafa-audio-setup-$CTID"
pct exec "$PROXY_CT" -- test ! -e "$SETUP" || fail "Proxy-Setup-Verzeichnis bereits vorhanden"
pct exec "$PROXY_CT" -- mkdir -m 0700 "$SETUP"
for file in install-nginx-proxy.sh render-nginx-proxy.py check-proxy-host.py install-duckdns-updater.sh duckdns-update.py; do
  pct push "$PROXY_CT" "$SRC/proxmox/$file" "$SETUP/$file"
done
pct exec "$PROXY_CT" -- bash "$SETUP/install-nginx-proxy.sh" prepare "$HOST" "$NEW_IP" --shared

printf '\n=== Neue TAFA-Sprachinstallation wiederaufgenommen ===\n'
pct exec "$CTID" -- /usr/local/sbin/tafa-info || true
printf '\nZertifikat anschliessend auf dem Proxy CT %s ausstellen:\n' "$PROXY_CT"
printf '  pct enter %s\n' "$PROXY_CT"
printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$HOST" "$HOST"
printf '  bash %s/install-nginx-proxy.sh enable %s %s --shared\n' "$SETUP" "$HOST" "$NEW_IP"
printf 'Falls DuckDNS-IPv4-Aktualisierung gewuenscht:\n'
printf '  bash %s/install-duckdns-updater.sh %s\n' "$SETUP" "$HOST"
printf 'Die alte TAFA-Installation und CT 101 Sites bleiben unveraendert.\n'
