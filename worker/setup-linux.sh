#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"
if [[ -e .env ]]; then echo 'Existing .env preserved.'; exit 0; fi
command -v docker >/dev/null || { echo 'Install Docker Engine, Compose and NVIDIA Container Toolkit first.' >&2; exit 1; }
docker info >/dev/null
read -r -p 'Private IPv4 address of this GPU host: ' ip
python3 - "$ip" <<'PY2'
import ipaddress, json, subprocess, sys, os
ip=ipaddress.IPv4Address(sys.argv[1])
if not any(ip in ipaddress.ip_network(net) for net in ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16')):
    raise SystemExit('Use a private IPv4 address.')
interfaces=json.loads(subprocess.check_output(['ip','-j','address','show'],text=True))
if not any(x.get('local')==str(ip) and x.get('family')=='inet' for entry in interfaces for x in entry.get('addr_info',[])):
    raise SystemExit('Address is not on this host.')
with os.fdopen(os.open('.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
    f.write(f'LAN_IP={ip}\nQWEN_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice\nQWEN_SPEAKER=Ryan\n')
print('Configuration saved without API tokens. Keep ports on trusted LAN only.')
PY2
docker compose config --quiet
echo 'Start with: docker compose up -d --build whisper'
