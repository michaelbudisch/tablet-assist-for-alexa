#!/usr/bin/env bash
# Optional split DNS inside an existing Debian NGINX guest. Never edit NGINX or HA.
set -Eeuo pipefail
[[ $EUID -eq 0 && -r /etc/debian_version && -d /run/systemd/system ]] || { echo "Run as root inside a Debian systemd guest." >&2; exit 1; }
if command -v pveversion >/dev/null 2>&1; then echo "Do not run on the Proxmox host." >&2; exit 1; fi
DIR=$(cd "$(dirname "$0")" && pwd)
CONF=/etc/dnsmasq.d/tafa-local-https.conf
[[ $# -ge 1 ]] || { echo "Usage: $0 {install HOST PROXY_LAN_IP ROUTER_DNS_IP|remove}" >&2; exit 2; }
case "$1" in
  install)
    [[ $# -eq 4 ]] || { echo "Usage: $0 install HOST PROXY_LAN_IP ROUTER_DNS_IP" >&2; exit 2; }
    [[ ! -e "$CONF" && ! -L "$CONF" ]] || { echo "TAFA DNS file exists; refusing overwrite." >&2; exit 1; }
    command -v nginx >/dev/null && systemctl is-active --quiet nginx || { echo "Requires an already running NGINX." >&2; exit 1; }
    command -v python3 >/dev/null && command -v ss >/dev/null || { echo "Requires Python 3 and ss (iproute2)." >&2; exit 1; }
    TMP=$(mktemp)
    trap 'rm -f "$TMP"' EXIT
    python3 "$DIR/render-local-https-dns.py" "$2" "$3" "$4" > "$TMP"
    if command -v dnsmasq >/dev/null 2>&1 || ss -H -lntup '( sport = :53 )' | grep -q .; then
      echo "Port 53/DNS already in use. Configure existing DNS manually; nothing changed." >&2
      exit 1
    fi
    apt-get update
    apt-get install -y dnsmasq
    if ! grep -Eq '^[[:space:]]*conf-dir=/etc/dnsmasq\.d([,[:space:]]|$)' /etc/dnsmasq.conf; then
      systemctl disable --now dnsmasq >/dev/null 2>&1 || true
      echo "Expected Debian dnsmasq conf-dir setting missing; no file created." >&2
      exit 1
    fi
    install -d -m 0755 /etc/dnsmasq.d
    install -m 0644 "$TMP" "$CONF"
    if ! dnsmasq --test || ! systemctl enable --now dnsmasq || ! systemctl restart dnsmasq || ! systemctl is-active --quiet dnsmasq; then
      rm -f "$CONF"
      systemctl disable --now dnsmasq >/dev/null 2>&1 || true
      echo "Setup failed; TAFA DNS file removed and service stopped." >&2
      exit 1
    fi
    echo "Local DNS active. Test from LAN: nslookup $2 $3"
    ;;
  remove)
    [[ $# -eq 1 ]] || { echo "Usage: $0 remove" >&2; exit 2; }
    [[ -f "$CONF" && ! -L "$CONF" ]] || { echo "No TAFA DNS file; nothing changed."; exit 0; }
    [[ $(head -n 1 "$CONF") == '# Managed by TAFA optional local HTTPS DNS setup.' ]] || {
      echo "File not owned by TAFA; refusing removal." >&2; exit 1;
    }
    rm "$CONF"
    systemctl disable --now dnsmasq
    echo "Local DNS removed. Restore tablet DNS to DHCP."
    ;;
  *) echo "Usage: $0 {install HOST PROXY_LAN_IP ROUTER_DNS_IP|remove}" >&2; exit 2 ;;
esac
