#!/usr/bin/env bash
# Optional interactive DuckDNS update client in the EXISTING central Nginx CT.
# DuckDNS domain must already have been added on www.duckdns.org.
# Do not paste the account token into chat, command lines, or logs.
set -Eeuo pipefail
umask 077
[[ "$EUID" == 0 && -t 0 && -r /dev/tty ]] || {
  echo "Run interactively as root INSIDE the Nginx proxy CT."; exit 1;
}
[[ -f /etc/debian_version && -d /run/systemd/system ]] || {
  echo "Debian systemd guest required"; exit 1;
}
command -v pveversion >/dev/null && { echo "Do not install on PVE host"; exit 1; }
[[ $# -eq 1 ]] || { echo "Usage: bash install-duckdns-updater.sh LABEL.duckdns.org"; exit 2; }
DOMAIN="$1"
if [[ ! "$DOMAIN" =~ ^[a-z0-9][a-z0-9-]{0,61}\.duckdns\.org$ ]]; then
  echo "Use a registered DuckDNS domain label (lowercase), e.g. example.duckdns.org"; exit 2
fi
LABEL="\${DOMAIN%.duckdns.org}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$HERE/duckdns-update.py" ]] || { echo "Missing updater source"; exit 1; }
install -d -m 0700 /etc/tafa-duckdns
DEST="/etc/tafa-duckdns/$LABEL.json"
if [[ -e "$DEST" || -L "$DEST" ]]; then
  echo "This domain already has a local updater; no changes made."; exit 1
fi
for unit in /etc/systemd/system/tafa-duckdns@.service /etc/systemd/system/tafa-duckdns@.timer; do
  [[ ! -e "$unit" && ! -L "$unit" ]] || {
    echo "TAFA updater systemd template already exists. Check manually; no overwrite."; exit 1;
  }
done
if [[ -e /usr/local/lib/tafa-duckdns-update.py ]]; then
  echo "Updater binary already installed; refusing to overwrite."; exit 1
fi

echo "DuckDNS domain: $DOMAIN"
echo "Create it on https://www.duckdns.org before this step."
printf 'Is the domain registered under YOUR DuckDNS account? Type JA: '
IFS= read -r CONFIRM </dev/tty
[[ "$CONFIRM" == JA ]] || { echo "Cancelled, nothing changed."; exit 1; }
printf 'DuckDNS account token (hidden; needed ONLY for DuckDNS IP updates): ' >/dev/tty
IFS= read -r -s TOKEN </dev/tty
printf '\n' >/dev/tty
[[ "$TOKEN" =~ ^[0-9A-Za-z_-]{16,128}$ ]] || { echo "Invalid token format"; unset TOKEN; exit 1; }
install -m 0600 /dev/null "$DEST"
printf '{"domain":"%s","token":"%s"}\n' "$DOMAIN" "$TOKEN" > "$DEST"
unset TOKEN
chmod 0600 "$DEST"
install -d -m 0755 /usr/local/lib
install -m 0755 "$HERE/duckdns-update.py" /usr/local/lib/tafa-duckdns-update.py

cat > /etc/systemd/system/tafa-duckdns@.service <<'EOF'
[Unit]
Description=Update registered DuckDNS IPv4 record for TAFA %i
After=network-online.target
Wants=network-online.target
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /usr/local/lib/tafa-duckdns-update.py /etc/tafa-duckdns/%i.json
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
EOF
cat > /etc/systemd/system/tafa-duckdns@.timer <<'EOF'
[Unit]
Description=Keep registered DuckDNS IPv4 record updated (%i)
[Timer]
OnBootSec=2min
OnUnitActiveSec=10min
Persistent=true
[Install]
WantedBy=timers.target
EOF
chmod 0644 /etc/systemd/system/tafa-duckdns@.service /etc/systemd/system/tafa-duckdns@.timer
systemctl daemon-reload
# Check the registration/token before installing the recurring timer.
if ! systemctl start "tafa-duckdns@$LABEL.service"; then
  echo "DuckDNS update failed. Timer not enabled; check the domain/token and logs."
  echo "Local secret file is at $DEST and remains private; remove it if unused."
  exit 1
fi
systemctl enable --now "tafa-duckdns@$LABEL.timer"
printf 'DuckDNS IPv4 update active for %s (every 10 minutes)\n' "$DOMAIN"
echo "No public ports, Nginx sites or other DuckDNS domains changed."
