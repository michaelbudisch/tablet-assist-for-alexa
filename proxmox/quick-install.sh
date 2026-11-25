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
# With an existing public Nginx CT, keep router 80/443 unchanged.
# The new CT is only the fresh speech backend; the shared proxy gets a NEW site.
printf '\nHTTPS-Modus: dedicated = neuer CT mit eigenem Nginx/Portweiterleitung;\n'
printf '            shared = bereits vorhandener zentraler Nginx-CT;\n'
printf '            none = noch kein oeffentlicher HTTPS-Zugriff.\n'
ask "HTTPS-Modus (dedicated/shared/none)" "dedicated"
PUBLIC_MODE="$REPLY_VALUE"
PROXY_CT=""
PROXY_IP=""
case "$PUBLIC_MODE" in
  dedicated) : ;;
  none)
    [[ -z "$PUBLIC_HOST" ]] || die "Fuer eine Domain bitte dedicated oder shared waehlen."
    ;;
  shared)
    [[ -n "$PUBLIC_HOST" ]] || die "Shared-Proxy-Modus erfordert einen neuen Audio-Hostnamen."
    ask "CT-ID des vorhandenen zentralen Nginx-Proxys" "101"
    PROXY_CT="$REPLY_VALUE"
    [[ "$PROXY_CT" =~ ^[1-9][0-9]{2,7}$ && "$PROXY_CT" != "$CTID" ]] || die "Ungueltige Proxy-ID."
    [[ "$(pct status "$PROXY_CT" 2>/dev/null)" == *running* ]] || die "Proxy CT laeuft nicht."
    pct exec "$PROXY_CT" -- nginx -t || die "Vorhandener Nginx hat Konfigurationsfehler."
    pct exec "$PROXY_CT" -- bash -lc 'command -v certbot >/dev/null' || die "Certbot fehlt auf Proxy-CT."
    if pct exec "$PROXY_CT" -- test -e /etc/nginx/sites-available/tablet-assist-audio; then
      die "Ein TAFA Audio-vHost existiert bereits auf dem Proxy; nicht ueberschreiben."
    fi
    PROXY_IP="$(pct exec "$PROXY_CT" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
    [[ -n "$PROXY_IP" ]] || die "Keine private IPv4-Adresse des Proxy-CT gefunden."
    printf 'Bestehender Proxy-CT %s hat LAN-IP %s und behaelt 80/443.\n' "$PROXY_CT" "$PROXY_IP"
    printf 'Es wird spaeter nur eine NEUE Audio-Site hinzugefuegt, keine bestehende veraendert.\n'
    ;;
  *) die "Nur dedicated, shared oder none moeglich." ;;
esac
if [[ "$PUBLIC_HOST" == *.duckdns.org ]]; then
  printf '\nDuckDNS: Domain %s vorher unter https://www.duckdns.org registrieren.\n' "$PUBLIC_HOST"
  printf 'Der DuckDNS-Update-Token bleibt privat und ist KEIN TAFA-API-Token.\n'
fi
printf '\nNEUER CT %s | %s CPU | %s MiB RAM | %s GiB | %s\n' "$CTID" "$CORES" "$RAM" "$DISK" "$STORE"
printf 'Netzwerk %s | Qwen: %s | HTTPS-Hostname: %s\n' "$NET" "$GPU_BASE" "$PUBLIC_HOST"
printf 'HTTPS-Modus: %s | bestehender Proxy-CT: %s\n' "$PUBLIC_MODE" "${PROXY_CT:-keiner}"
if [[ "$PUBLIC_MODE" == shared ]]; then
  printf 'Zusatz-Bestaetigung: Eine neue Nginx-Site auf CT %s vorbereiten? JA eintippen: ' "$PROXY_CT"
  IFS= read -r PROXY_CONFIRM </dev/tty
  [[ "$PROXY_CONFIRM" == JA ]] || die "Proxy-Aenderung nicht bestaetigt; nichts erstellt."
fi
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
if [[ "$PUBLIC_MODE" == shared ]]; then
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "$PUBLIC_HOST" "$GPU_BASE" shared "$PROXY_IP" "$PROXY_CT" "$CTID"
  NEW_CT_IP="$(pct exec "$CTID" -- hostname -I | tr ' ' '\n' | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)"
  [[ -n "$NEW_CT_IP" ]] || die "Neuer CT hat noch keine private IPv4."
  PROXY_SETUP="/opt/tafa-audio-setup-$CTID"
  pct exec "$PROXY_CT" -- test ! -e "$PROXY_SETUP" || die "Das Verzeichnis $PROXY_SETUP ist belegt."
  pct exec "$PROXY_CT" -- mkdir -m 0700 "$PROXY_SETUP"
  for filename in install-nginx-proxy.sh render-nginx-proxy.py check-proxy-host.py install-duckdns-updater.sh duckdns-update.py; do
    pct push "$PROXY_CT" "$SOURCE/proxmox/$filename" "$PROXY_SETUP/$filename"
  done
  # Existing sites are never edited. Prepare only a new hostname and ACME webroot.
  pct exec "$PROXY_CT" -- bash "$PROXY_SETUP/install-nginx-proxy.sh" prepare "$PUBLIC_HOST" "$NEW_CT_IP" --shared
  printf '\nNEUE Domain vorbereitet auf CT %s, ohne bestehende Sites zu veraendern.\n' "$PROXY_CT"
  printf 'Wenn DNS aktuell ist, auf dem Proxmox-Host diese Schritte ausfuehren:\n'
  printf '  pct enter %s\n' "$PROXY_CT"
  printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$PUBLIC_HOST" "$PUBLIC_HOST"
  printf '  bash %s/install-nginx-proxy.sh enable %s %s --shared\n' "$PROXY_SETUP" "$PUBLIC_HOST" "$NEW_CT_IP"
  if [[ "$PUBLIC_HOST" == *.duckdns.org ]]; then
    printf '\nOPTIONAL: Neue DuckDNS-Domain automatisch aktuell halten (nur einmal im CT %s):\n' "$PROXY_CT"
    printf '  bash %s/install-duckdns-updater.sh %s\n' "$PROXY_SETUP" "$PUBLIC_HOST"
    printf 'Den DuckDNS-Account-Token dort verdeckt eingeben, niemals im Chat oder in Git.\n'
  fi
elif [[ "$PUBLIC_MODE" == none ]]; then
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "" "$GPU_BASE"
else
  pct exec "$CTID" -- bash /opt/tafa-installer/proxmox/install-combined-ct.sh "$PUBLIC_HOST" "$GPU_BASE"
fi
printf '\n=== Installation beendet: CT %s ===\n' "$CTID"
pct exec "$CTID" -- /usr/local/sbin/tafa-info || true
printf '\nProxmox → CT %s → Konsole: dauerhafte Statusinfos.\n' "$CTID"
printf 'PVE-Shell: pct enter %s\n' "$CTID"
printf 'Im CT: tafa-info (Status) | tafa-setup (HTTPS-Assistent)\n'
if [[ "$PUBLIC_MODE" == shared ]]; then
  printf 'Der bisherige Proxy CT %s bleibt oeffentlicher HTTPS-Eingang; keine Routerumstellung.\n' "$PROXY_CT"
  printf 'Die neue Domain wird erst nach Certbot und enable erreichbar.\n'
  printf 'DuckDNS-Aktualisierung bei dynamischer oeffentlicher IP separat einrichten.\n'
else
  printf 'DNS und Router werden bewusst nicht automatisch umgestellt.\n'
fi
CREATED=0
