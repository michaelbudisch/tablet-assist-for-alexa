#!/usr/bin/env bash
# Only inside a fresh dedicated Debian guest created by quick-install.sh.
# Install one Piper/Whisper/MP3 backend + localhost-only Nginx MP3 HTTPS frontend.
set -Eeuo pipefail
umask 077
[[ "$EUID" == 0 && -f /etc/debian_version && -d /run/systemd/system ]] || {
  echo "Debian systemd CT required"; exit 1;
}
if command -v pveversion >/dev/null; then echo "Refusing to run on PVE host"; exit 1; fi
[[ $# -eq 1 ]] || { echo "Usage: install-combined-ct.sh [PUBLIC_AUDIO_HOST]"; exit 2; }
HOST="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$HERE/install-speechserver.sh" && -f "$HERE/install-nginx-proxy.sh" && -f "$HERE/combined-console.sh" ]] || {
  echo "Complete TAFA installer archive required"; exit 1;
}
[[ ! -e /opt/jarvis-local && ! -e /etc/tafa-combined-hostname ]] || {
  echo "Existing installation detected. Refusing to overwrite."; exit 1;
}

# Do not weaken or replace a running Nginx configuration on an existing CT.
if systemctl list-unit-files nginx.service --no-legend 2>/dev/null | grep -q '^nginx'; then
  echo "Nginx already installed. Use a fresh CT."; exit 1
fi

bash "$HERE/install-speechserver.sh"

# The MP3 file server must not be exposed on the LAN on a combined CT.
# The audio Nginx proxy connects to loopback:8080 only.
install -d -m 0755 /etc/systemd/system/jarvis-audio.service.d
cat > /etc/systemd/system/jarvis-audio.service.d/10-loopback.conf <<'EOF'
[Service]
ExecStart=
ExecStart=/opt/jarvis-local/venv/bin/waitress-serve --listen=127.0.0.1:8080 --threads=2 audio_server:app
EOF
systemctl daemon-reload
systemctl restart jarvis-audio.service
systemctl is-active --quiet jarvis-audio.service || { echo "Audio service failed"; exit 1; }

apt-get update
apt-get install -y nginx certbot
install -m 0755 "$HERE/combined-console.sh" /usr/local/sbin/tafa-info
ln -s /usr/local/sbin/tafa-info /usr/local/sbin/tafa-setup
install -m 0600 /dev/null /etc/tafa-combined-hostname
printf '%s\n' "$HOST" > /etc/tafa-combined-hostname
if [[ -n "$HOST" ]]; then
  bash "$HERE/install-nginx-proxy.sh" prepare "$HOST" 127.0.0.1
else
  echo "Kein öffentlicher Hostname angegeben: Nginx installiert, HTTPS bleibt deaktiviert."
  systemctl enable --now nginx
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
printf '\nWICHTIG: Neues TLS-Zertifikat nur nach DNS-/Router-Einrichtung per tafa-setup aktivieren.\n'
printf 'Ports 5000, 5001, 10300: nur vertrauenswürdiges LAN, keinesfalls Internet-Freigaben.\n'
