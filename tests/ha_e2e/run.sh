#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="$(mktemp -d)"
name="tablet-assist-ci-$"
network="$name-net"
image="ghcr.io/home-assistant/home-assistant:2026.11.0"
cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker network rm "$network" >/dev/null 2>&1 || true
  # HA may create root-owned storage directories inside the temporary mount.
  sudo rm -rf -- "$work"
}
trap cleanup EXIT
mkdir -p "$work/custom_components"
cp -a "$root/custom_components/tablet_assist_for_alexa" "$work/custom_components/"
cp -a "$root/tests/ha_e2e/fixture" "$work/custom_components/tablet_assist_ci"
cat > "$work/configuration.yaml" <<'YAML'
homeassistant:
  name: Tablet Assist CI
  time_zone: UTC
  unit_system: metric
frontend:
http:
conversation:
persistent_notification:
tablet_assist_ci:
YAML
docker pull "$image"
# A private bridge supplies an interface for HA Zeroconf/mDNS without
# publishing ports or allowing external network egress during tests.
docker network create --driver bridge --internal "$network" >/dev/null
run_phase(){
  local phase="$1" limit="$2"
  docker run -d --name "$name" --network "$network" \
    -e "TABLET_ASSIST_CI_PHASE=$phase" -v "$work:/config" \
    --entrypoint python3 "$image" -m homeassistant --config /config
  local result="$work/ci-result-$phase.json"
  for ((i=0; i<limit; i++)); do
    if [[ -f "$result" ]]; then
      cat "$result"
      jq -e '.ok == true' "$result" || { docker logs --tail 180 "$name"; return 1; }
      return 0
    fi
    if [[ "$(docker inspect --format '{{.State.Running}}' "$name")" != true ]]; then
      docker logs --tail 180 "$name"
      return 1
    fi
    sleep 1
  done
  docker logs --tail 180 "$name"
  echo "Timed out waiting for $phase"
  return 1
}
run_phase one 210
docker stop --time 20 "$name"
docker rm "$name"
run_phase two 270
echo "HA standalone integration, reload, local queries and persistent reminder passed."
