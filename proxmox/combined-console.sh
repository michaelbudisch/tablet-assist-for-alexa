#!/usr/bin/env bash
# TAFA combined Debian guest: live status, pre-login banner and guided TLS setup.
set -Eeuo pipefail
export LC_ALL=C
HOSTFILE=/etc/tafa-combined-hostname
INSTALLER=/opt/tafa-installer/proxmox/install-nginx-proxy.sh
RENDER=/opt/tafa-installer/proxmox/render-nginx-proxy.py

get_host() {
  HOST=""
  MODE="dedicated"
  PROXY_IP=""
  PROXY_CT=""
  NEW_CT=""
  if [[ -f /etc/tafa-shared-proxy-ct ]]; then
    IFS= read -r PROXY_CT </etc/tafa-shared-proxy-ct || true
  fi
  if [[ -f /etc/tafa-new-ct-id ]]; then
    IFS= read -r NEW_CT </etc/tafa-new-ct-id || true
  fi
  if [[ -f "$HOSTFILE" ]]; then
    IFS= read -r HOST < "$HOSTFILE" || true
  fi
  if [[ -f /etc/tafa-proxy-mode ]]; then
    IFS= read -r MODE </etc/tafa-proxy-mode || true
  fi
  if [[ -f /etc/tafa-shared-proxy-ip ]]; then
    IFS= read -r PROXY_IP </etc/tafa-shared-proxy-ip || true
  fi
}
get_ip() {
  IP="$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -n1 || true)"
  [[ -n "$IP" ]] || IP="no IPv4 address yet"
}
svc() {
  if systemctl is-active --quiet "$1.service" 2>/dev/null; then
    printf 'running'
  else
    printf 'stopped'
  fi
}
tls_status() {
  HTTPS="not configured"
  if [[ "$MODE" == shared ]]; then
    HTTPS="Central proxy $PROXY_IP (check HTTPS on proxy)"
    return
  fi
  if [[ -n "$HOST" && -r "/etc/letsencrypt/live/$HOST/fullchain.pem" &&
        -r "/etc/letsencrypt/live/$HOST/privkey.pem" &&
        -f "/etc/nginx/sites-enabled/tablet-assist-audio" ]]; then
    if grep -q 'listen 443 ssl' /etc/nginx/sites-available/tablet-assist-audio 2>/dev/null &&
        systemctl is-active --quiet nginx; then
      HTTPS="https://$HOST (certificate available)"
    fi
  fi
}
show_status() {
  get_ip
  get_host
  tls_status
  printf '\n============================================================\n'
  printf ' TAFA | Speech services and Alexa MP3 delivery\n'
  printf '============================================================\n'
  printf ' LAN IPv4    : %s\n' "$IP"
  printf ' Piper TTS   : http://%s:5000 | %s\n' "$IP" "$(svc jarvis-piper)"
  printf ' Alexa MP3   : http://%s:5001 | %s\n' "$IP" "$(svc jarvis-mp3)"
  printf ' Wyoming STT : %s:10300 | %s\n' "$IP" "$(svc jarvis-whisper)"
  if [[ "$MODE" == shared ]]; then
    printf ' MP3 files : %s:8080 (only proxy %s is allowed)\n' "$IP" "$PROXY_IP"
  else
    printf ' MP3 files : 127.0.0.1:8080 (loopback only)\n'
  fi
  if [[ -f /etc/jarvis-local.env ]]; then
    GPU="$(sed -n 's/^JARVIS_GPU_BASE=//p' /etc/jarvis-local.env | head -n1)"
  else
    GPU=""
  fi
  if [[ -n "$GPU" ]]; then
    printf ' Qwen Worker : %s (used for MP3 generation when ready)\n' "$GPU"
  else
    printf ' Qwen Worker : not configured (using Piper)\n'
  fi
  if [[ "$MODE" == shared ]]; then
    printf ' Nginx       : existing central proxy CT %s (%s)\n' "$PROXY_CT" "$PROXY_IP"
  else
    printf ' Nginx       : %s\n' "$(svc nginx)"
  fi
  printf ' Alexa HTTPS : %s\n' "$HTTPS"
  if [[ -n "$HOST" ]]; then printf ' Audio domain: %s\n' "$HOST"; fi
  printf '\n Home Assistant / TAFA App:\n'
  printf '   External Piper: http://%s:5000\n' "$IP"
  printf '   Wyoming (STT):  %s:10300\n' "$IP"
  printf '   MP3-Generator:  http://%s:5001\n' "$IP"
  if [[ "$MODE" == shared ]]; then
    printf '   Audio-HTTPS:    https://%s (check on central proxy)\n' "$HOST"
  fi
  if [[ "$HTTPS" == https://* ]]; then
    printf '   Alexa Audio:    https://%s\n' "$HOST"
  else
    printf '   Alexa Audio:    not enabled yet\n'
  fi
  printf '\n Commands: tafa-info | tafa-setup | journalctl -u jarvis-mp3 -n 30\n'
  printf ' Network: Never expose internal service ports to the Internet.\n'
  if [[ "$MODE" == shared ]]; then
    printf ' Shared proxy: Finish HTTPS configuration on proxy CT %s.\n' "$PROXY_CT"
    printf ' Help: tafa-setup (prints commands for proxy CT %s)\n' "$PROXY_CT"
  fi
  printf '============================================================\n'
}
refresh_banner() {
  [[ "$EUID" == 0 ]] || { echo 'Root required'; exit 1; }
  get_ip
  get_host
  tls_status
  BANNER="$(cat <<EOF
TAFA - Proxmox speech services
IP: $IP
Piper http://$IP:5000 | MP3 http://$IP:5001 | Wyoming $IP:10300
Nginx: $HTTPS
Proxy mode: $MODE
After login: tafa-info (live status), tafa-setup (HTTPS wizard)
Private LAN only. Never expose MP3 generation to the Internet.

EOF
)"
  printf '%s\n' "$BANNER" > /etc/issue
  printf '%s\n' "$BANNER" > /etc/motd
}
validate_host() {
  python3 "$RENDER" "$1" 127.0.0.1 >/dev/null
  [[ "$1" != *.local ]] || { echo "A .local hostname cannot be used as a public audio domain."; return 1; }
}
prepare_host() {
  get_host
  if [[ -z "$HOST" ]]; then
    printf '\nPublic Alexa audio hostname (without https://): '
    IFS= read -r HOST
    [[ -n "$HOST" ]] || { echo "Cancelled."; return 1; }
    validate_host "$HOST" || { echo 'Invalid hostname.'; return 1; }
    bash "$INSTALLER" prepare "$HOST" 127.0.0.1
    printf '%s\n' "$HOST" > "$HOSTFILE"
    chmod 0600 "$HOSTFILE"
    refresh_banner
  fi
}
enable_https() {
  [[ "$EUID" == 0 && -t 0 ]] || { echo "Root in interrunninger CT-Konsole erforderlich."; return 1; }
  get_host
  if [[ "$MODE" == shared ]]; then
    get_ip
    echo "Existing Nginx proxy CT $PROXY_CT ($PROXY_IP) serves $HOST."
    echo "Register and update the domain at https://www.duckdns.org first."
    echo "Keep existing router port forwards unchanged. On the Proxmox host:"
    printf '  pct enter %s\n' "$PROXY_CT"
    echo "Then INSIDE THE PROXY CT:"
    printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$HOST" "$HOST"
    printf '  bash /opt/tafa-audio-setup-%s/install-nginx-proxy.sh enable %s %s --shared\n' "$NEW_CT" "$HOST" "$IP"
    if [[ "$HOST" == *.duckdns.org ]]; then
      echo "Optional DuckDNS IP updater:"
      printf '  bash /opt/tafa-audio-setup-%s/install-duckdns-updater.sh %s\n' "$NEW_CT" "$HOST"
      echo "Enter the DuckDNS account token privately in the proxy CT, never in chat."
    fi
    return 0
  fi
  prepare_host || return 1
  get_host
  tls_status
  if [[ "$HTTPS" == https://* ]]; then
    echo "HTTPS is already enabled: $HTTPS"
    return 0
  fi
  if [[ ! -f /etc/nginx/sites-available/tablet-assist-audio ]]; then
    echo "Nginx audio site is missing; check the installation."; return 1
  fi
  printf '\nBefore requesting a certificate, verify:\n'
  printf '  - Public DNS name %s points to your public IP address.\n' "$HOST"
  printf '  - TCP ports 80 and 443 reach this Nginx CT with no conflicting port forwards.\n'
  printf '  - Never forward ports 5000, 5001, 8080 or 10300 to the Internet.\n'
  printf 'Are these prerequisites in place? Type YES: '
  IFS= read -r ANSWER
  [[ "$ANSWER" == "YES" ]] || { echo "No changes made; run this wizard again later."; return 1; }
  certbot certonly --webroot -w /var/lib/tablet-assist-acme \
    --cert-name "$HOST" -d "$HOST"
  bash "$INSTALLER" enable "$HOST" 127.0.0.1
  refresh_banner
  echo "HTTPS is enabled. Configure Alexa audio URL in TAFA as https://$HOST."
}
run_wizard() {
  [[ "$EUID" == 0 && -t 0 ]] || { echo "Als root interrunning im CT ausfuehren."; exit 1; }
  while true; do
    printf '\nTAFA setup (speech services)\n'
    printf '  1) Show service status and Home Assistant endpoints\n'
    printf '  2) Enable Alexa HTTPS with DNS and Certbot\n'
    printf '  3) Show detailed Piper/MP3/Whisper/Nginx service status\n'
    printf '  4) Refresh the console login banner\n'
    printf '  0) Exit\nSelect: '
    IFS= read -r SELECTED
    case "$SELECTED" in
      1) show_status ;;
      2) enable_https || true ;;
      3) systemctl --no-pager --full status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio nginx || true ;;
      4) refresh_banner; echo "Console banner updated." ;;
      0) return 0 ;;
      *) echo "Choose a number from 0 to 4." ;;
    esac
  done
}
case "$0" in
  tafa-setup|*/tafa-setup) run_wizard ;;
  *)
    case "$*" in
      --refresh-banner) refresh_banner ;;
      ""|--status) show_status ;;
      *) printf 'Usage: tafa-info [--refresh-banner|--status]\n' >&2; exit 2 ;;
    esac
    ;;
esac
