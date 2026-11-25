#!/usr/bin/env bash
# Only inside a fresh dedicated Debian guest created by quick-install.sh.
# Install one Piper/Whisper/MP3 backend + localhost-only Nginx MP3 HTTPS frontend.
set -Eeuo pipefail
umask 077
[[ "$EUID" == 0 && -f /etc/debian_version && -d /run/systemd/system ]] || {
  echo "Debian systemd CT required"; exit 1;
}
if command -v pveversion >/dev/null; then echo "Refusing to run on PVE host"; exit 1; fi
[[ $# -eq 2 || $# -eq 6 ]] || { echo "Usage: install-combined-ct.sh HOST GPU_BASE [shared PROXY_IPV4 PROXY_CT NEW_CT]"; exit 2; }
HOST="$1"
GPU_BASE="$2"
MODE="dedicated"
PROXY_IP=""
PROXY_CT=""
NEW_CT=""
if [[ $# -eq 6 ]]; then
  [[ "$3" == shared ]] || { echo "Only shared proxy mode is supported"; exit 2; }
  MODE=shared
  PROXY_IP="$4"
  PROXY_CT="$5"
  NEW_CT="$6"
  [[ "$PROXY_CT" =~ ^[1-9][0-9]{2,7}$ && "$NEW_CT" =~ ^[1-9][0-9]{2,7}$ ]] || { echo "Invalid CT ID"; exit 2; }
  python3 - "$PROXY_IP" <<'PY'
import ipaddress,sys
ip=ipaddress.ip_address(sys.argv[1])
assert isinstance(ip,ipaddress.IPv4Address) and ip.is_private and not ip.is_loopback
PY
fi
HERE="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$HERE/install-speechserver.sh" && -f "$HERE/install-nginx-proxy.sh" && -f "$HERE/combined-console.sh" ]] || {
  echo "Complete TAFA installer archive required"; exit 1;
}
[[ ! -e /opt/jarvis-local && ! -e /etc/tafa-combined-hostname ]] || {
  echo "Existing installation detected. Refusing to overwrite."; exit 1;
}

# Do not weaken or replace a running Nginx configuration on an existing CT.
if [[ "$MODE" == dedicated ]] && systemctl list-unit-files nginx.service --no-legend 2>/dev/null | grep -q '^nginx'; then
  echo "Nginx already installed. Use a fresh CT."; exit 1
fi

bash "$HERE/install-speechserver.sh"
# Connect the MP3 Qwen route only when the user explicitly supplied a LAN worker.
if [[ -n "$GPU_BASE" ]]; then
  python3 - "$GPU_BASE" <<'PY'
import ipaddress,sys
from urllib.parse import urlsplit
u=urlsplit(sys.argv[1])
assert u.scheme=="http" and u.hostname and u.port and not any((u.username,u.password,u.path,u.query,u.fragment))
try:
  ip=ipaddress.ip_address(u.hostname)
  assert ip.version==4 and ip.is_private and not ip.is_loopback
except ValueError:
  assert u.hostname.endswith(".local") and len(u.hostname)<254
PY
  sed -i "s|^JARVIS_GPU_BASE=.*$|JARVIS_GPU_BASE=$GPU_BASE|" /etc/jarvis-local.env
  systemctl restart jarvis-mp3.service
fi

if [[ "$MODE" == shared ]]; then
  # Existing central Nginx on another CT retains all public HTTPS traffic.
  # The temporary MP3 file server is LAN-reachable only for the chosen proxy.
  # Other clients, including unknown LAN nodes, receive 404.
  printf 'JARVIS_AUDIO_ALLOW_IP=%s\n' "$PROXY_IP" >> /etc/jarvis-local.env
  systemctl restart jarvis-audio.service
  echo "Shared mode: Nginx remains on the existing proxy CT."
else
  # New standalone installation: Nginx talks only to this CT's loopback.
  install -d -m 0755 /etc/systemd/system/jarvis-audio.service.d
  cat > /etc/systemd/system/jarvis-audio.service.d/10-loopback.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/jarvis-local/venv/bin/waitress-serve --listen=127.0.0.1:8080 --threads=2 audio_server:app
EOF
  systemctl daemon-reload
  systemctl restart jarvis-audio.service
  apt-get update
  apt-get install -y nginx certbot
fi
systemctl is-active --quiet jarvis-audio.service || { echo "Audio service failed"; exit 1; }
install -m 0755 "$HERE/combined-console.sh" /usr/local/sbin/tafa-info
ln -s /usr/local/sbin/tafa-info /usr/local/sbin/tafa-setup
printf '%s\n' "$HOST" > /etc/tafa-combined-hostname
printf '%s\n' "$MODE" > /etc/tafa-proxy-mode
printf '%s\n' "$PROXY_IP" > /etc/tafa-shared-proxy-ip
printf '%s\n' "$PROXY_CT" > /etc/tafa-shared-proxy-ct
printf '%s\n' "$NEW_CT" > /etc/tafa-new-ct-id
chmod 0600 /etc/tafa-combined-hostname /etc/tafa-proxy-mode /etc/tafa-shared-proxy-ip /etc/tafa-shared-proxy-ct /etc/tafa-new-ct-id
if [[ "$MODE" == dedicated ]]; then
  if [[ -n "$HOST" ]]; then
    bash "$HERE/install-nginx-proxy.sh" prepare "$HOST" 127.0.0.1
  else
    echo "Kein öffentlicher Hostname: Nginx installiert, HTTPS bleibt deaktiviert."
    if [[ -L /etc/nginx/sites-enabled/default &&
          $(readlink /etc/nginx/sites-enabled/default) == /etc/nginx/sites-available/default ]]; then
      rm /etc/nginx/sites-enabled/default
    fi
    nginx -t
    systemctl enable --now nginx
    systemctl reload nginx
  fi
fi
install -d -m 0755 /etc/profile.d
cat > /etc/profile.d/tafa-status.sh <<'EOF'
# Show live TAFA service endpoints at interactive shell login.
if [ -t 1 ] && [ -x /usr/local/sbin/tafa-info ]; then
  /usr/local/sbin/tafa-info
fi
EOF
chmod 0644 /etc/profile.d/tafa-status.sh
cat >/etc/systemd/system/tafa-console-info.service <<'EOF'
[Unit]
Description=Refresh TAFA LXC console login banner
After=network-online.target
Wants=network-online.target
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/tafa-info --refresh-banner
EOF
cat >/etc/systemd/system/tafa-console-info.timer <<'EOF'
[Unit]
Description=Refresh TAFA console IP and service status every 5 minutes
[Timer]
OnBootSec=20s
OnUnitActiveSec=5min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now tafa-console-info.timer
/usr/local/sbin/tafa-info --refresh-banner
/usr/local/sbin/tafa-info
if [[ "$MODE" == shared ]]; then
  printf '\nWICHTIG: Die HTTPS-Zertifikate werden ausschließlich auf dem bestehenden Proxy installiert.\n'
else
  printf '\nWICHTIG: TLS nur nach DNS-/Router-Einrichtung per tafa-setup aktivieren.\n'
fi
printf 'Ports 5000, 5001, 10300: nur vertrauenswürdiges LAN, keinesfalls Internet-Freigaben.\n'
