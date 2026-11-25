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
die() { printf '\nFEHLER: %s\n' "$*" >&2; exit 1; }
on_error() {
  if (( CREATED )); then
    printf '\nFehler nach CT-Erstellung. Container %s bleibt zur Diagnose erhalten.\n' "$CTID" >&2
    printf 'Im PVE-Host: pct enter %s\n' "$CTID" >&2
  fi
}
cleanup() { if [[ -n "$WORK" && -d "$WORK" ]]; then rm -rf -- "$WORK"; fi; }
trap on_error ERR
trap cleanup EXIT
[[ "$EUID" == 0 && -t 0 && -r /dev/tty ]] || die "Als root in einer interaktiven Proxmox-Shell starten."
for cmd in pct qm pvesh pvesm pveam pveversion curl tar awk grep sort python3; do
  command -v "$cmd" >/dev/null || die "PVE-Werkzeug fehlt: $cmd"
done
ask() {
  local label="$1" fallback="$2" answer
  printf '%s [%s]: ' "$label" "$fallback" >/dev/tty
  IFS= read -r answer </dev/tty
  REPLY_VALUE="$answer"
  [[ -n "$REPLY_VALUE" ]] || REPLY_VALUE="$fallback"
}
optional() {
  printf '%s (leer=spaeter): ' "$1" >/dev/tty
  IFS= read -r REPLY_VALUE </dev/tty
}
printf '\n=== TAFA: Ein CT fuer Piper, Whisper, MP3 und Nginx ===\n'
printf 'Gefuehrter Installer. Neue, unprivilegierte Debian-Umgebung.\n'
printf 'Keine bestehende CT-/VM-Konfiguration und keine Routerfreigaben werden geaendert.\n\n'
NEXT="$(pvesh get /cluster/nextid 2>/dev/null | tr -dc '0-9' | head -c 8 || true)"
[[ "$NEXT" =~ ^[1-9][0-9]{2,7}$ ]] || NEXT=105
ask "Freie CT-ID" "$NEXT"
CTID="$REPLY_VALUE"
[[ "$CTID" =~ ^[1-9][0-9]{2,7}$ ]] || die "Ungueltige ID."
if pct config "$CTID" >/dev/null 2>&1 || qm config "$CTID" >/dev/null 2>&1 || [[ -e "/etc/pve/lxc/$CTID.conf" || -e "/etc/pve/qemu-server/$CTID.conf" ]]; then
  die "Diese CT-/VM-ID ist bereits belegt."
fi
ROOT_STORES="$(pvesm status --content rootdir | awk 'NR>1 && $3=="active" {print $1}')"
[[ -n "$ROOT_STORES" ]] || die "Kein Rootfs-Speicher verfuegbar."
printf '\nCT-Speicher:\n%s\n' "$ROOT_STORES"
DEFAULT_STORE="$(printf '%s\n' "$ROOT_STORES" | grep -Fx local-lvm | head -n1 || true)"
[[ -n "$DEFAULT_STORE" ]] || DEFAULT_STORE="$(printf '%s\n' "$ROOT_STORES" | head -n1)"
ask "Rootfs-Speicher" "$DEFAULT_STORE"
STORE="$REPLY_VALUE"
printf '%s\n' "$ROOT_STORES" | grep -Fxq -- "$STORE" || die "Rootfs-Speicher nicht verfuegbar."
TPL_STORES="$(pvesm status --content vztmpl | awk 'NR>1 && $3=="active" {print $1}')"
[[ -n "$TPL_STORES" ]] || die "Kein Template-Speicher verfuegbar."
printf '\nTemplate-Speicher:\n%s\n' "$TPL_STORES"
DEFAULT_TPL="$(printf '%s\n' "$TPL_STORES" | grep -Fx local | head -n1 || true)"
[[ -n "$DEFAULT_TPL" ]] || DEFAULT_TPL="$(printf '%s\n' "$TPL_STORES" | head -n1)"
ask "Template-Speicher" "$DEFAULT_TPL"
TPL_STORE="$REPLY_VALUE"
printf '%s\n' "$TPL_STORES" | grep -Fxq -- "$TPL_STORE" || die "Template-Speicher nicht verfuegbar."
ask "Netzwerkbridge" "vmbr0"
BRIDGE="$REPLY_VALUE"
[[ "$BRIDGE" =~ ^[a-zA-Z0-9_.-]+$ && -d "/sys/class/net/$BRIDGE" ]] || die "Bridge existiert nicht."
ask "Netzwerk: dhcp oder static" "dhcp"
case "$REPLY_VALUE" in
  dhcp) NET="name=eth0,bridge=$BRIDGE,ip=dhcp" ;;
  static)
    ask "Statische IP/CIDR" "192.168.1.90/24"; IP="$REPLY_VALUE"
    ask "Standardgateway" "192.168.1.1"; GW="$REPLY_VALUE"
    python3 - "$IP" "$GW" <<'PY' || die "Statische Netzwerkadresse ungueltig."
import sys,ipaddress
n=ipaddress.ip_interface(sys.argv[1])
g=ipaddress.ip_address(sys.argv[2])
assert isinstance(n,ipaddress.IPv4Interface) and n.ip.is_private
assert isinstance(g,ipaddress.IPv4Address) and g in n.network
PY
    NET="name=eth0,bridge=$BRIDGE,ip=$IP,gw=$GW"
    ;;
  *) die "Netzwerkmodus ungueltig." ;;
esac
ask "CPU-Kerne" "4"; CORES="$REPLY_VALUE"
ask "RAM in MiB" "4096"; RAM="$REPLY_VALUE"
ask "Festplatte in GiB" "32"; DISK="$REPLY_VALUE"
[[ "$CORES" =~ ^[0-9]+$ && "$RAM" =~ ^[0-9]+$ && "$DISK" =~ ^[0-9]+$ ]] || die "Ressourcen muessen Zahlen sein."
(( CORES>=2 && CORES<=64 && RAM>=2048 && RAM<=131072 && DISK>=24 && DISK<=2048 )) || die "Ressourcen ausserhalb sinnvoller Grenzen."
optional "Optionaler GPU-Worker fuer Qwen-MP3 (http://LAN-IP:10502)"
GPU_BASE="$REPLY_VALUE"
if [[ -n "$GPU_BASE" ]]; then
  python3 - "$GPU_BASE" <<'PY' || die "GPU-Adresse muss eine private HTTP-LAN-Adresse ohne Pfad sein."
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
optional "Oeffentlicher Alexa-Audiohostname (ohne https://)"
PUBLIC_HOST="$REPLY_VALUE"
if [[ -n "$PUBLIC_HOST" ]]; then
  python3 - "$PUBLIC_HOST" <<'PY' || die "Oeffentlicher Hostname ist ungueltig."
import re,sys
host=sys.argv[1].lower()
label=r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
assert len(host)<=253 and re.fullmatch(label+r"(?:\."+label+r")+",host)
assert not host.endswith(".local")
PY
fi
printf '\nNEUER CT %s | %s CPU | %s MiB RAM | %s GiB | %s\n' "$CTID" "$CORES" "$RAM" "$DISK" "$STORE"
printf 'Netzwerk %s | Qwen: %s | HTTPS-Hostname: %s\n' "$NET" "$GPU_BASE" "$PUBLIC_HOST"
printf 'CT-ID %s zur endgueltigen Bestaetigung eintippen: ' "$CTID" >/dev/tty
IFS= read -r CONFIRM </dev/tty
[[ "$CONFIRM" == "$CTID" ]] || die "Abgebrochen, nichts erstellt."

WORK="$(mktemp -d /tmp/tafa-pve.XXXXXXXX)"
curl -fLSs --retry 2 --connect-timeout 15 --max-time 180 "$REPO" -o "$WORK/repo.tar.gz"
tar -xzf "$WORK/repo.tar.gz" -C "$WORK"
SOURCE="$WORK/tablet-assist-for-alexa-main"
for file in proxmox/install-speechserver.sh proxmox/install-nginx-proxy.sh proxmox/install-combined-ct.sh proxmox/combined-console.sh speechserver/api.py; do
  [[ -f "$SOURCE/$file" ]] || die "Repository-Datei fehlt: $file"
done
pveam update
TEMPLATE="$(pveam available --section system | awk '$2 ~ /^debian-13-standard_.*_amd64.tar.zst$/ {print $2}' | sort -V | tail -n1)"
[[ -n "$TEMPLATE" ]] || TEMPLATE="$(pveam available --section system | awk '$2 ~ /^debian-12-standard_.*_amd64.tar.zst$/ {print $2}' | sort -V | tail -n1)"
[[ "$TEMPLATE" =~ ^debian-1[23]-standard_[A-Za-z0-9._-]+_amd64.tar.zst$ ]] || die "Kein Debian 12/13 AMD64-Template gefunden."
if ! pveam list "$TPL_STORE" | grep -Fq "vztmpl/$TEMPLATE"; then
  pveam download "$TPL_STORE" "$TEMPLATE"
fi
if pct config "$CTID" >/dev/null 2>&1 || qm config "$CTID" >/dev/null 2>&1; then
  die "Die ID wurde zwischenzeitlich belegt."
fi
printf '\nLege neuen CT %s an ...\n' "$CTID"
pct create "$CTID" "$TPL_STORE:vztmpl/$TEMPLATE" \
  --hostname tafa-voice --unprivileged 1 --ostype debian \
  --cores "$CORES" --memory "$RAM" --swap 1024 --rootfs "$STORE:$DISK" \
  --net0 "$NET" --onboot 1
CREATED=1
pct start "$CTID"
tar -C "$SOURCE" -czf "$WORK/installer.tar.gz" speechserver proxmox
pct push "$CTID" "$WORK/installer.tar.gz" /tmp/tafa-installer.tar.gz
pct exec "$CTID" -- mkdir -p /opt/tafa-installer
pct exec "$CTID" -- tar -xzf /tmp/tafa-installer.tar.gz -C /opt/tafa-installer
pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "$PUBLIC_HOST" "$GPU_BASE"
printf '\n=== Installation beendet: CT %s ===\n' "$CTID"
pct exec "$CTID" -- /usr/local/sbin/tafa-info || true
printf '\nProxmox → CT %s → Konsole: dauerhafte Statusinfos.\n' "$CTID"
printf 'PVE-Shell: pct enter %s\n' "$CTID"
printf 'Im CT: tafa-info (Status) | tafa-setup (HTTPS-Assistent)\n'
printf 'DNS und Router werden bewusst nicht automatisch umgestellt.\n'
CREATED=0
