#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -eq 0 ]] && command -v pct >/dev/null || { echo "Run on Proxmox VE as administrator."; exit 1; }
[[ $# -ge 5 && $# -le 6 ]] || { echo "Usage: create-proxy-ct.sh CTID TEMPLATE_VOLUME STORAGE PUBLIC_HOST SPEECHSERVER_HOST [BRIDGE]"; exit 2; }
ID=$1; TEMPLATE=$2; STORE=$3; HOST=$4; UPSTREAM=$5
BRIDGE=vmbr0
if [[ $# -eq 6 ]]; then BRIDGE=$6; fi
[[ "$ID" =~ ^[0-9]+$ ]] || exit 2
if pct config "$ID" >/dev/null 2>&1 || qm config "$ID" >/dev/null 2>&1; then echo "CT ID already in use."; exit 1; fi
DIR=$(cd "$(dirname "$0")" && pwd)
python3 "$DIR/render-nginx-proxy.py" "$HOST" "$UPSTREAM" >/dev/null
printf 'Proxy container hostname [tablet-assist-proxy]: ' >/dev/tty
IFS= read -r CT_HOSTNAME </dev/tty
CT_HOSTNAME="${CT_HOSTNAME:-tablet-assist-proxy}"
[[ ${#CT_HOSTNAME} -le 63 && "$CT_HOSTNAME" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || {
  echo 'Invalid hostname: use lowercase letters, digits or hyphens (1-63 chars).' >&2
  exit 2
}
[[ "$CT_HOSTNAME" != localhost ]] || { echo 'Hostname localhost is reserved.' >&2; exit 2; }
printf 'Create NEW unprivileged proxy CT %s (%s; 1 vCPU, 512 MiB RAM, 4 GiB, DHCP)? Type CT ID: ' "$ID" "$CT_HOSTNAME"
printf 'Proxmox will securely prompt for the new CT root password during creation.\n'
read -r confirm </dev/tty
[[ "$confirm" == "$ID" ]] || exit 1
pct create "$ID" "$TEMPLATE" --hostname "$CT_HOSTNAME" --unprivileged 1 --cores 1 --memory 512 --swap 512 --rootfs "$STORE:4" --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" --onboot 1 --password
pct start "$ID"
pct exec "$ID" -- mkdir -p /opt/tablet-assist-proxy
pct push "$ID" "$DIR/install-nginx-proxy.sh" /opt/tablet-assist-proxy/install-nginx-proxy.sh
pct push "$ID" "$DIR/render-nginx-proxy.py" /opt/tablet-assist-proxy/render-nginx-proxy.py
pct exec "$ID" -- bash /opt/tablet-assist-proxy/install-nginx-proxy.sh prepare "$HOST" "$UPSTREAM"
pct exec "$ID" -- hostname -I
echo "Proxy prepared. Complete DNS and certificate setup as documented. No host/router ports have been altered."
