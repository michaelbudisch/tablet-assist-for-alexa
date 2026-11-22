#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="$(mktemp -d)"
name="echo-relay-camera-ci-${BASHPID}"
network="$name-net"
cleanup(){
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
  sudo rm -rf -- "$work"
}
trap cleanup EXIT
mkdir -p "$work/custom_components"
cp -a "$root/homeassistant/custom_components/jarvis_tablet_audio" "$work/custom_components/"
cp -a "$root/tests/relay_camera_e2e/fixture" "$work/custom_components/relay_camera_ci"
cat > "$work/configuration.yaml" <<'YAML'
homeassistant:
  name: Echo Relay camera CI
  time_zone: UTC
http:
camera:
conversation:
relay_camera_ci:
YAML
image="ghcr.io/home-assistant/home-assistant:2026.11.0"
docker pull "$image"
docker network create --driver bridge --internal "$network" >/dev/null
docker run -d --name "$name" --network "$network" -v "$work:/config" --entrypoint python3 "$image" -m homeassistant --config /config
for ((i=0;i<180;i++)); do
  if [[ -f "$work/result.json" ]]; then
    cat "$work/result.json"
    jq -e '.ok == true' "$work/result.json" || { docker logs --tail 100 "$name"; exit 1; }
    exit 0
  fi
  sleep 1
done
docker logs --tail 100 "$name"
echo 'Camera receiver runtime check timed out'
exit 1
