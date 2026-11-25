#!/usr/bin/env bash
# TAFA: guided one-command installation in a NEW Proxmox VE LXC.
# Existing CTs, VMs, DNS, existing Nginx sites and router remain untouched.
set -Eeuo pipefail
export LC_ALL=C
umask 077
REPO="https://github.com/michaelbudisch/tablet-assist-for-alexa/archive/refs/heads/main.tar.gz"
WORK=""
CREATED=0
CTID=""
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }
on_error() {
  if (( CREATED )); then
    printf '\nInstallation failed after CT %s was created. The CT remains available for troubleshooting.\n' "$CTID" >&2
    printf 'On the PVE host: pct enter %s\n' "$CTID" >&2
  fi
}
cleanup() { if [[ -n "$WORK" && -d "$WORK" ]]; then rm -rf -- "$WORK"; fi; }
trap on_error ERR
trap cleanup EXIT
[[ "$EUID" == 0 && -t 0 && -r /dev/tty ]] || die "Run as root in an interactive Proxmox VE host shell."
for cmd in pct qm pvesh pvesm pveam pveversion curl tar awk grep sort python3; do
  command -v "$cmd" >/dev/null || die "Missing Proxmox tool: $cmd"
done
ask() {
  local label="$1" fallback="$2" answer
  printf '%s [%s]: ' "$label" "$fallback" >/dev/tty
  IFS= read -r answer </dev/tty
  REPLY_VALUE="$answer"
  [[ -n "$REPLY_VALUE" ]] || REPLY_VALUE="$fallback"
}
optional() {
  printf '%s (leave blank to configure later): ' "$1" >/dev/tty
  IFS= read -r REPLY_VALUE </dev/tty
}
printf '\n=== TAFA: Guided speech server installer ===\n'
printf 'A new unprivileged Debian CT will be created.\n'
printf 'Existing CTs/VMs, proxy websites and router port forwards will not be changed.\n\n'
NEXT="$(pvesh get /cluster/nextid 2>/dev/null | tr -dc '0-9' | head -c 8 || true)"
[[ "$NEXT" =~ ^[1-9][0-9]{2,7}$ ]] || NEXT=105
ask "Unused CT ID" "$NEXT"
CTID="$REPLY_VALUE"
[[ "$CTID" =~ ^[1-9][0-9]{2,7}$ ]] || die "Invalid CT ID."
if pct config "$CTID" >/dev/null 2>&1 || qm config "$CTID" >/dev/null 2>&1 || [[ -e "/etc/pve/lxc/$CTID.conf" || -e "/etc/pve/qemu-server/$CTID.conf" ]]; then
  die "This CT/VM ID is already in use."
fi
ask "Container hostname" "tafa-voice"
CT_HOSTNAME="$REPLY_VALUE"
# A single DNS label only: prevent spaces, metacharacters and invalid hostname characters.
[[ ${#CT_HOSTNAME} -le 63 && "$CT_HOSTNAME" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || \
  die "Invalid hostname: use 1-63 lowercase letters, digits or hyphens, without leading/trailing hyphens."
[[ "$CT_HOSTNAME" != localhost ]] || die "The hostname 'localhost' is reserved."
ROOT_STORES="$(pvesm status --content rootdir | awk 'NR>1 && $3=="active" {print $1}')"
[[ -n "$ROOT_STORES" ]] || die "No active container root filesystem storage is available."
printf '\nContainer storage:\n%s\n' "$ROOT_STORES"
DEFAULT_STORE="$(printf '%s\n' "$ROOT_STORES" | grep -Fx local-lvm | head -n1 || true)"
[[ -n "$DEFAULT_STORE" ]] || DEFAULT_STORE="$(printf '%s\n' "$ROOT_STORES" | head -n1)"
ask "Root filesystem storage" "$DEFAULT_STORE"
STORE="$REPLY_VALUE"
printf '%s\n' "$ROOT_STORES" | grep -Fxq -- "$STORE" || die "The selected root filesystem storage is unavailable."
TPL_STORES="$(pvesm status --content vztmpl | awk 'NR>1 && $3=="active" {print $1}')"
[[ -n "$TPL_STORES" ]] || die "No active template storage is available."
printf '\nTemplate storage:\n%s\n' "$TPL_STORES"
DEFAULT_TPL="$(printf '%s\n' "$TPL_STORES" | grep -Fx local | head -n1 || true)"
[[ -n "$DEFAULT_TPL" ]] || DEFAULT_TPL="$(printf '%s\n' "$TPL_STORES" | head -n1)"
ask "Template storage" "$DEFAULT_TPL"
TPL_STORE="$REPLY_VALUE"
printf '%s\n' "$TPL_STORES" | grep -Fxq -- "$TPL_STORE" || die "The selected template storage is unavailable."
ask "Network bridge" "vmbr0"
BRIDGE="$REPLY_VALUE"
[[ "$BRIDGE" =~ ^[a-zA-Z0-9_.-]+$ && -d "/sys/class/net/$BRIDGE" ]] || die "Network bridge does not exist."
ask "Network mode (dhcp/static)" "dhcp"
case "$REPLY_VALUE" in
  dhcp) NET="name=eth0,bridge=$BRIDGE,ip=dhcp" ;;
  static)
    ask "Static IPv4/CIDR" "192.168.1.90/24"; IP="$REPLY_VALUE"
    ask "Default gateway" "192.168.1.1"; GW="$REPLY_VALUE"
    python3 - "$IP" "$GW" <<'PY' || die "Invalid static IPv4 address or gateway."
import sys,ipaddress
n=ipaddress.ip_interface(sys.argv[1])
g=ipaddress.ip_address(sys.argv[2])
assert isinstance(n,ipaddress.IPv4Interface) and n.ip.is_private
assert isinstance(g,ipaddress.IPv4Address) and g in n.network
PY
    NET="name=eth0,bridge=$BRIDGE,ip=$IP,gw=$GW"
    ;;
  *) die "Invalid network mode; choose dhcp or static." ;;
esac
ask "CPU cores" "4"; CORES="$REPLY_VALUE"
ask "RAM in MiB" "4096"; RAM="$REPLY_VALUE"
ask "Disk size in GiB" "32"; DISK="$REPLY_VALUE"
[[ "$CORES" =~ ^[0-9]+$ && "$RAM" =~ ^[0-9]+$ && "$DISK" =~ ^[0-9]+$ ]] || die "CPU, RAM and disk must be whole numbers."
(( CORES>=2 && CORES<=64 && RAM>=2048 && RAM<=131072 && DISK>=24 && DISK<=2048 )) || die "Resources out of supported range: 2-64 CPU, 2048-131072 MiB RAM, 24-2048 GiB disk."
optional "Optional Qwen GPU worker URL (http://LAN-IP:10502)"
GPU_BASE="$REPLY_VALUE"
if [[ -n "$GPU_BASE" ]]; then
  python3 - "$GPU_BASE" <<'PY' || die "GPU URL must be a private HTTP LAN URL with a port and no path."
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
fi
optional "Public Alexa audio hostname (without https://)"
PUBLIC_HOST="$REPLY_VALUE"
if [[ -n "$PUBLIC_HOST" ]]; then
  python3 - "$PUBLIC_HOST" <<'PY' || die "Invalid public audio hostname."
import re,sys
host=sys.argv[1].lower()
label=r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
assert len(host)<=253 and re.fullmatch(label+r"(?:\."+label+r")+",host)
assert not host.endswith(".local")
PY
fi
# With an existing public Nginx CT, keep router 80/443 unchanged.
# The new CT is only the fresh speech backend; the shared proxy gets a NEW site.
printf '\nHTTPS mode: dedicated = new CT runs its own Nginx;\n'
printf '            shared = use an existing central Nginx proxy CT;\n'
printf '            none = no public HTTPS yet.\n'
ask "HTTPS mode (dedicated/shared/none)" "dedicated"
PUBLIC_MODE="$REPLY_VALUE"
PROXY_CT=""
PROXY_IP=""
case "$PUBLIC_MODE" in
  dedicated) : ;;
  none)
    [[ -z "$PUBLIC_HOST" ]] || die "Choose dedicated or shared when a public hostname was supplied."
    ;;
  shared)
    [[ -n "$PUBLIC_HOST" ]] || die "Shared proxy mode requires an audio hostname."
    ask "Existing central Nginx proxy CT ID" "101"
    PROXY_CT="$REPLY_VALUE"
    [[ "$PROXY_CT" =~ ^[1-9][0-9]{2,7}$ && "$PROXY_CT" != "$CTID" ]] || die "Invalid proxy CT ID."
    [[ "$(pct status "$PROXY_CT" 2>/dev/null)" == *running* ]] || die "Proxy CT is not running."
    pct exec "$PROXY_CT" -- nginx -t || die "Existing Nginx configuration failed validation."
    pct exec "$PROXY_CT" -- bash -lc 'command -v certbot >/dev/null' || die "Certbot is missing in the proxy CT."
    if pct exec "$PROXY_CT" -- test -e /etc/nginx/sites-available/tablet-assist-audio; then
      die "A TAFA audio site already exists on the proxy; refusing to overwrite it."
    fi
    PROXY_IP="$(pct exec "$PROXY_CT" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
    [[ -n "$PROXY_IP" ]] || die "Could not find a private IPv4 address on the proxy CT."
    printf 'Existing proxy CT %s uses LAN IP %s and keeps ports 80/443.\n' "$PROXY_CT" "$PROXY_IP"
    printf 'Only one NEW audio site will be added; existing sites will not be changed.\n'
    ;;
  *) die "Choose dedicated, shared or none." ;;
esac
if [[ "$PUBLIC_HOST" == *.duckdns.org ]]; then
  printf '\nDuckDNS: Register %s at https://www.duckdns.org before proceeding.\n' "$PUBLIC_HOST"
  printf 'Keep your DuckDNS account token private; it is NOT a TAFA API token.\n'
fi
printf '\nNEW CT %s | Hostname: %s | %s CPU | %s MiB RAM | %s GiB disk | %s\n' "$CTID" "$CT_HOSTNAME" "$CORES" "$RAM" "$DISK" "$STORE"
printf 'Network: %s | Qwen: %s | Public hostname: %s\n' "$NET" "$GPU_BASE" "$PUBLIC_HOST"
printf 'HTTPS mode: %s | Existing proxy CT: %s\n' "$PUBLIC_MODE" "${PROXY_CT:-none}"
if [[ "$PUBLIC_MODE" == shared ]]; then
  printf 'Confirmation: Prepare one NEW Nginx site on CT %s? Type YES: ' "$PROXY_CT"
  IFS= read -r PROXY_CONFIRM </dev/tty
  [[ "$PROXY_CONFIRM" == YES ]] || die "Proxy site addition not confirmed; nothing created."
fi
printf 'Final confirmation: Type CT ID %s: ' "$CTID" >/dev/tty
IFS= read -r CONFIRM </dev/tty
[[ "$CONFIRM" == "$CTID" ]] || die "Cancelled; no new CT was created."

WORK="$(mktemp -d /tmp/tafa-pve.XXXXXXXX)"
curl -fLSs --retry 2 --connect-timeout 15 --max-time 180 "$REPO" -o "$WORK/repo.tar.gz"
tar -xzf "$WORK/repo.tar.gz" -C "$WORK"
SOURCE="$WORK/tablet-assist-for-alexa-main"
for file in proxmox/install-speechserver.sh proxmox/install-nginx-proxy.sh proxmox/install-combined-ct.sh proxmox/combined-console.sh speechserver/api.py; do
  [[ -f "$SOURCE/$file" ]] || die "Missing repository file: $file"
done
pveam update
TEMPLATE="$(pveam available --section system | awk '$2 ~ /^debian-13-standard_.*_amd64.tar.zst$/ {print $2}' | sort -V | tail -n1)"
[[ -n "$TEMPLATE" ]] || TEMPLATE="$(pveam available --section system | awk '$2 ~ /^debian-12-standard_.*_amd64.tar.zst$/ {print $2}' | sort -V | tail -n1)"
[[ "$TEMPLATE" =~ ^debian-1[23]-standard_[A-Za-z0-9._-]+_amd64.tar.zst$ ]] || die "No supported Debian 12/13 AMD64 template found."
if ! pveam list "$TPL_STORE" | grep -Fq "vztmpl/$TEMPLATE"; then
  pveam download "$TPL_STORE" "$TEMPLATE"
fi
if pct config "$CTID" >/dev/null 2>&1 || qm config "$CTID" >/dev/null 2>&1; then
  die "The CT ID became unavailable during setup."
fi
printf '\nCreating new CT %s ...\n' "$CTID"
printf 'Set the CT root password when Proxmox prompts (input is hidden).\n'
printf 'This is the login for the CT console; the password will NOT be passed as a shell argument.\n'
# Proxmox VE 9 container bug #8295: umask 0077 makes the transient
# /var/lib/lxc/CTID/rootfs directories inaccessible to the mapped root
# of an unprivileged container during the archive extraction.
# Use the system-default umask only for pct create. Secrets and staging
# still use the restrictive umask 0077 set above.
(
  umask 0022
  pct create "$CTID" "$TPL_STORE:vztmpl/$TEMPLATE" \
    --hostname "$CT_HOSTNAME" --unprivileged 1 --ostype debian \
    --cores "$CORES" --memory "$RAM" --swap 1024 --rootfs "$STORE:$DISK" \
    --net0 "$NET" --onboot 1 --password
)
CREATED=1
pct start "$CTID"
tar -C "$SOURCE" -czf "$WORK/installer.tar.gz" speechserver proxmox
pct push "$CTID" "$WORK/installer.tar.gz" /tmp/tafa-installer.tar.gz
pct exec "$CTID" -- mkdir -p /opt/tafa-installer
pct exec "$CTID" -- tar -xzf /tmp/tafa-installer.tar.gz -C /opt/tafa-installer
if [[ "$PUBLIC_MODE" == shared ]]; then
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "$PUBLIC_HOST" "$GPU_BASE" shared "$PROXY_IP" "$PROXY_CT" "$CTID"
  NEW_CT_IP="$(pct exec "$CTID" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
  [[ -n "$NEW_CT_IP" ]] || die "The new CT has no private IPv4 address yet."
  PROXY_SETUP="/opt/tafa-audio-setup-$CTID"
  pct exec "$PROXY_CT" -- test ! -e "$PROXY_SETUP" || die "Proxy setup directory $PROXY_SETUP already exists; refusing to overwrite."
  pct exec "$PROXY_CT" -- mkdir -m 0700 "$PROXY_SETUP"
  for filename in install-nginx-proxy.sh render-nginx-proxy.py check-proxy-host.py install-duckdns-updater.sh duckdns-update.py; do
    pct push "$PROXY_CT" "$SOURCE/proxmox/$filename" "$PROXY_SETUP/$filename"
  done
  # Existing sites are never edited. Prepare only a new hostname and ACME webroot.
  pct exec "$PROXY_CT" -- bash "$PROXY_SETUP/install-nginx-proxy.sh" prepare "$PUBLIC_HOST" "$NEW_CT_IP" --shared
  printf '\nNEW audio domain prepared on CT %s; existing sites remain unchanged.\n' "$PROXY_CT"
  printf 'Once DNS is configured, complete these commands:\n'
  printf '  pct enter %s\n' "$PROXY_CT"
  printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$PUBLIC_HOST" "$PUBLIC_HOST"
  printf '  bash %s/install-nginx-proxy.sh enable %s %s --shared\n' "$PROXY_SETUP" "$PUBLIC_HOST" "$NEW_CT_IP"
  if [[ "$PUBLIC_HOST" == *.duckdns.org ]]; then
    printf '\nOPTIONAL: Keep this DuckDNS name updated (run once in proxy CT %s):\n' "$PROXY_CT"
    printf '  bash %s/install-duckdns-updater.sh %s\n' "$PROXY_SETUP" "$PUBLIC_HOST"
    printf 'Enter the DuckDNS token privately there; never paste it in chat or Git.\n'
  fi
elif [[ "$PUBLIC_MODE" == none ]]; then
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "" "$GPU_BASE"
else
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "$PUBLIC_HOST" "$GPU_BASE"
fi
printf '\n=== Installation completed: CT %s ===\n' "$CTID"
pct exec "$CTID" -- /usr/local/sbin/tafa-info || true
printf '\nProxmox > CT %s > Console: persistent endpoint and service information.\n' "$CTID"
printf 'PVE-Shell: pct enter %s\n' "$CTID"
printf 'Inside CT: tafa-info (status) | tafa-setup (HTTPS wizard) | tafa-export-json\n'
if [[ "$PUBLIC_MODE" == shared ]]; then
  printf 'Existing proxy CT %s remains the public HTTPS entry point; no router changes.\n' "$PROXY_CT"
  printf 'The new domain becomes available after certificate issuance and HTTPS activation.\n'
  printf 'Configure DuckDNS updates separately if your public IP changes.\n'
else
  printf 'DNS and router configuration are intentionally not changed automatically.\n'
fi
CREATED=0
