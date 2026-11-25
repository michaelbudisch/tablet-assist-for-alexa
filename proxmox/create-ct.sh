#!/usr/bin/env bash
# Explicit creation of a NEW unprivileged CT using an existing Debian template.
set -Eeuo pipefail
[[ $EUID -eq 0 ]] && command -v pct >/dev/null || { echo 'Run on Proxmox VE as administrator.'; exit 1; }
[[ $# -ge 3 && $# -le 4 ]] || { echo 'Usage: create-ct.sh CTID TEMPLATE_VOLUME STORAGE [BRIDGE]'; exit 2; }
ID=$1; TEMPLATE=$2; STORE=$3; BRIDGE=${4:-vmbr0}
[[ "$ID" =~ ^[0-9]+$ ]] || exit 2
if pct config "$ID" >/dev/null 2>&1 || qm config "$ID" >/dev/null 2>&1; then echo 'ID already in use'; exit 1; fi
ROOT=$(cd "$(dirname "$0")/.." && pwd)
printf 'Container hostname [jarvis-speechserver]: ' >/dev/tty
IFS= read -r CT_HOSTNAME </dev/tty
CT_HOSTNAME="${CT_HOSTNAME:-jarvis-speechserver}"
[[ ${#CT_HOSTNAME} -le 63 && "$CT_HOSTNAME" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || {
  echo 'Invalid hostname: use lowercase letters, digits or hyphens (1-63 chars).' >&2
  exit 2
}
[[ "$CT_HOSTNAME" != localhost ]] || { echo 'Hostname localhost is reserved.' >&2; exit 2; }
printf 'New CT %s (%s; 4 vCPU, 4 GiB RAM, 20 GiB disk, DHCP) on %s. Type the CT ID to confirm: ' "$ID" "$CT_HOSTNAME" "$BRIDGE"
printf 'Proxmox will securely prompt for the new CT root password during creation.\n'
read -r confirm </dev/tty
[[ "$confirm" == "$ID" ]] || exit 1
pct create "$ID" "$TEMPLATE" --hostname "$CT_HOSTNAME" --unprivileged 1 --cores 4 --memory 4096 --swap 1024 --rootfs "$STORE:20" --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" --onboot 1 --password
pct start "$ID"
ARCHIVE=$(mktemp --suffix=.tar.gz)
trap 'rm -f "$ARCHIVE"' EXIT
tar -C "$ROOT" -czf "$ARCHIVE" speechserver proxmox
pct push "$ID" "$ARCHIVE" /tmp/jarvis-install.tar.gz
pct exec "$ID" -- mkdir -p /opt/jarvis-installer
pct exec "$ID" -- tar -xzf /tmp/jarvis-install.tar.gz -C /opt/jarvis-installer
pct exec "$ID" -- bash /opt/jarvis-installer/proxmox/install-speechserver.sh
pct exec "$ID" -- hostname -I
printf 'CT %s created. Use the guest IP in Home Assistant. No firewall/router changes made.\n' "$ID"
