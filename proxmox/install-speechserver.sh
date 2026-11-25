#!/usr/bin/env bash
# Run as root INSIDE a dedicated Debian 12/13 VM or unprivileged container.
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo 'Run as root inside the speechserver guest.'; exit 1; }
[[ -r /etc/debian_version ]] || { echo 'Debian guest required.'; exit 1; }
if command -v pveversion >/dev/null; then echo 'Refusing to install on the Proxmox host.'; exit 1; fi
[[ -d /run/systemd/system ]] || { echo 'A systemd guest is required.'; exit 1; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL=/opt/jarvis-local
DATA=/var/lib/jarvis
ENV=/etc/jarvis-local.env
VOICE=${JARVIS_PIPER_VOICE:-de_DE-thorsten-medium}
MODEL=${JARVIS_WHISPER_MODEL:-small-int8}
[[ "$VOICE" =~ ^[A-Za-z0-9_-]+$ && "$MODEL" =~ ^[A-Za-z0-9_-]+$ ]] || exit 1
[[ ! -e "$INSTALL" && ! -e "$ENV" ]] || { echo 'Already installed or incomplete installation; do not overwrite.'; exit 1; }
for port in 5000 5001 8080 10300; do
    if ss -ltnH "sport = :$port" | grep -q .; then echo "Port $port already in use."; exit 1; fi
done
apt-get update
apt-get install -y python3 python3-venv python3-pip ffmpeg ca-certificates curl iproute2 libgomp1 libespeak-ng1 espeak-ng-data libsndfile1 libstdc++6
if ! id jarvis-local >/dev/null 2>&1; then useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin jarvis-local; fi
install -d -m 0755 "$INSTALL"
install -d -o jarvis-local -g jarvis-local -m 0750 "$DATA" "$DATA/audio" "$DATA/models" "$DATA/whisper"
install -m 0644 "$ROOT"/speechserver/{api.py,piper_service.py,audio_server.py,cleanup.py,requirements.txt} "$INSTALL/"
python3 -m venv "$INSTALL/venv"
"$INSTALL/venv/bin/pip" install --upgrade pip
"$INSTALL/venv/bin/pip" install -r "$INSTALL/requirements.txt"
runuser -u jarvis-local -- "$INSTALL/venv/bin/python" -m piper.download_voices --data-dir "$DATA/models" "$VOICE"
[[ -f "$DATA/models/$VOICE.onnx" ]] || { echo 'Voice model missing.'; exit 1; }
cat > "$ENV" <<EOF
JARVIS_GPU_BASE=
JARVIS_PIPER_URL=http://127.0.0.1:5000/synthesize
JARVIS_PIPER_MODEL=$DATA/models/$VOICE.onnx
JARVIS_AUDIO_DIR=$DATA/audio
EOF
chmod 0600 "$ENV"
# The ports below are LAN services. Restrict guest traffic to Home Assistant and
# the trusted optional reverse proxy using the Proxmox/network firewall.
for svc in piper mp3 audio whisper cleanup; do
  case "$svc" in
    piper) execstart="$INSTALL/venv/bin/waitress-serve --listen=0.0.0.0:5000 --threads=2 piper_service:app" ;;
    mp3) execstart="$INSTALL/venv/bin/waitress-serve --listen=0.0.0.0:5001 --threads=2 api:app" ;;
    audio) execstart="$INSTALL/venv/bin/waitress-serve --listen=0.0.0.0:8080 --threads=2 audio_server:app" ;;
    whisper) execstart="$INSTALL/venv/bin/python -m wyoming_faster_whisper --uri tcp://0.0.0.0:10300 --model $MODEL --language de --data-dir $DATA/whisper --download-dir $DATA/whisper --device cpu --compute-type int8" ;;
    cleanup) execstart="$INSTALL/venv/bin/python $INSTALL/cleanup.py" ;;
  esac
  type=simple; restart=on-failure
  [[ "$svc" != cleanup ]] || { type=oneshot; restart=no; }
  cat > "/etc/systemd/system/jarvis-$svc.service" <<EOF
[Unit]
Description=Jarvis $svc
After=network-online.target
Wants=network-online.target
[Service]
Type=$type
User=jarvis-local
Group=jarvis-local
WorkingDirectory=$INSTALL
EnvironmentFile=$ENV
Environment=HOME=$DATA
ExecStart=$execstart
Restart=$restart
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA
[Install]
WantedBy=multi-user.target
EOF
done
cat > /etc/systemd/system/jarvis-cleanup.timer <<'EOF'
[Unit]
Description=Expire temporary announcement files
[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now jarvis-piper.service jarvis-mp3.service jarvis-whisper.service jarvis-audio.service jarvis-cleanup.timer
for i in {1..30}; do
  if curl -fsS --max-time 2 http://127.0.0.1:5000/health >/dev/null && curl -fsS --max-time 2 http://127.0.0.1:5001/health; then
    echo; echo 'Piper and MP3 service are ready. Whisper downloads its model on first start.'
    echo 'Private LAN only: no additional TAFA API token is needed. Keep the generator port 5001 behind the LAN firewall.'
    exit 0
  fi
  sleep 2
done
journalctl -u jarvis-piper.service -u jarvis-mp3.service -n 30 --no-pager >&2
exit 1
