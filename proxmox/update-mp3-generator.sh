#!/usr/bin/env bash
# Update only the Jarvis MP3 API inside an existing dedicated Debian speech guest.
# No data/voice/service rewrite; original python file backed up with a timestamp.
set -Eeuo pipefail
[[ $EUID -eq 0 && -f /etc/debian_version && -d /run/systemd/system ]] || { echo 'Root in a Debian systemd guest required'; exit 1; }
if command -v pveversion >/dev/null; then echo 'Refusing to run on Proxmox host'; exit 1; fi
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/speechserver/api.py"
DST=/opt/jarvis-local/api.py
[[ -f "$SRC" && -f "$DST" && ! -L "$DST" ]] || { echo 'Speechserver API source or installed API missing'; exit 1; }
systemctl cat jarvis-mp3.service >/dev/null || { echo 'Existing jarvis-mp3.service missing'; exit 1; }
if grep -q 'PIPER_API_TOKEN\|JARVIS_TTS_TOKEN\|X-API-Key' "$SRC"; then echo 'Source still requires an API key'; exit 1; fi
python3 -m py_compile "$SRC"
if cmp -s "$SRC" "$DST"; then echo 'MP3 API already current; no changes'; exit 0; fi
umask 077
BACKUP=/var/backups/jarvis-mp3-api
install -d -m 0700 "$BACKUP"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
cp -p -- "$DST" "$BACKUP/api.py.$STAMP"
cp -- "$SRC" "$DST"
chown --reference="$BACKUP/api.py.$STAMP" "$DST"
chmod --reference="$BACKUP/api.py.$STAMP" "$DST"
if ! systemctl restart jarvis-mp3.service || ! systemctl is-active --quiet jarvis-mp3.service; then
  cp -p -- "$BACKUP/api.py.$STAMP" "$DST"
  systemctl restart jarvis-mp3.service || true
  echo "MP3 service update failed; prior API restored from $BACKUP/api.py.$STAMP" >&2
  exit 1
fi
if ! curl -fsS --max-time 5 http://127.0.0.1:5001/health >/dev/null; then
  cp -p -- "$BACKUP/api.py.$STAMP" "$DST"
  systemctl restart jarvis-mp3.service || true
  echo 'MP3 service health failed; prior API restored' >&2
  exit 1
fi
echo "MP3 generator updated; no token needed. Backup: $BACKUP/api.py.$STAMP"
echo "IMPORTANT: port 5001 is internal LAN only. Keep external HTTPS proxy MP3 GET only."
