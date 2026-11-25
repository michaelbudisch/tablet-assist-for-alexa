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
  [[ -n "$IP" ]] || IP="noch keine IPv4-Adresse"
}
svc() {
  if systemctl is-active --quiet "$1.service" 2>/dev/null; then
    printf 'aktiv'
  else
    printf 'nicht aktiv'
  fi
}
tls_status() {
  HTTPS="noch nicht eingerichtet"
  if [[ "$MODE" == shared ]]; then
    HTTPS="Zentraler Proxy $PROXY_IP (HTTPS dort pruefen)"
    return
  fi
  if [[ -n "$HOST" && -r "/etc/letsencrypt/live/$HOST/fullchain.pem" &&
        -r "/etc/letsencrypt/live/$HOST/privkey.pem" &&
        -f "/etc/nginx/sites-enabled/tablet-assist-audio" ]]; then
    if grep -q 'listen 443 ssl' /etc/nginx/sites-available/tablet-assist-audio 2>/dev/null &&
        systemctl is-active --quiet nginx; then
      HTTPS="https://$HOST (Zertifikat vorhanden)"
    fi
  fi
}
show_status() {
  get_ip
  get_host
  tls_status
  printf '\n============================================================\n'
  printf ' TAFA | Sprachserver + Alexa-MP3 + Nginx (ein Proxmox-CT)\n'
  printf '============================================================\n'
  printf ' LAN IPv4    : %s\n' "$IP"
  printf ' Piper TTS   : http://%s:5000 | %s\n' "$IP" "$(svc jarvis-piper)"
  printf ' Alexa MP3   : http://%s:5001 | %s\n' "$IP" "$(svc jarvis-mp3)"
  printf ' Wyoming STT : %s:10300 | %s\n' "$IP" "$(svc jarvis-whisper)"
  if [[ "$MODE" == shared ]]; then
    printf ' MP3-Dateien : %s:8080 (nur Proxy %s erlaubt)\n' "$IP" "$PROXY_IP"
  else
    printf ' MP3-Dateien : 127.0.0.1:8080 (nur lokal im CT)\n'
  fi
  if [[ -f /etc/jarvis-local.env ]]; then
    GPU="$(sed -n 's/^JARVIS_GPU_BASE=//p' /etc/jarvis-local.env | head -n1)"
  else
    GPU=""
  fi
  if [[ -n "$GPU" ]]; then
    printf ' Qwen Worker : %s (MP3-Erzeugung, falls bereit)\n' "$GPU"
  else
    printf ' Qwen Worker : nicht konfiguriert (Piper wird verwendet)\n'
  fi
  if [[ "$MODE" == shared ]]; then
    printf ' Nginx       : externer zentraler Proxy CT %s (%s)\n' "$PROXY_CT" "$PROXY_IP"
  else
    printf ' Nginx       : %s\n' "$(svc nginx)"
  fi
  printf ' Alexa HTTPS : %s\n' "$HTTPS"
  if [[ -n "$HOST" ]]; then printf ' Audio-Domain: %s\n' "$HOST"; fi
  printf '\n Home Assistant / TAFA App:\n'
  printf '   Externer Piper: http://%s:5000\n' "$IP"
  printf '   Wyoming (STT):  %s:10300\n' "$IP"
  printf '   MP3-Generator:  http://%s:5001\n' "$IP"
  if [[ "$MODE" == shared ]]; then
    printf '   Audio-HTTPS:    https://%s (auf zentralem Proxy pruefen)\n' "$HOST"
  fi
  if [[ "$HTTPS" == https://* ]]; then
    printf '   Alexa Audio:    https://%s\n' "$HOST"
  else
    printf '   Alexa Audio:    noch nicht freigeschaltet\n'
  fi
  printf '\n Befehle: tafa-info | tafa-setup | journalctl -u jarvis-mp3 -n 30\n'
  printf ' Netzwerk: Interne Ports nicht ins Internet weiterleiten.\n'
  if [[ "$MODE" == shared ]]; then
    printf ' Shared-Modus: HTTPS-Einrichtung auf Proxy CT %s abschliessen.\n' "$PROXY_CT"
    printf ' Anleitung: tafa-setup (zeigt Befehle fuer Proxy CT %s)\n' "$PROXY_CT"
  fi
  printf '============================================================\n'
}
refresh_banner() {
  [[ "$EUID" == 0 ]] || { echo 'Root required'; exit 1; }
  get_ip
  get_host
  tls_status
  BANNER="$(cat <<EOF
TAFA - kombinierter Proxmox-Sprachserver
IP: $IP
Piper http://$IP:5000 | MP3 http://$IP:5001 | Wyoming $IP:10300
Nginx: $HTTPS
Proxy-Modus: $MODE
Nach Login: tafa-info (Live-Status), tafa-setup (HTTPS-Assistent)
Nur fuer das lokale Netzwerk; keine MP3-API an das Internet weiterleiten.

EOF
)"
  printf '%s\n' "$BANNER" > /etc/issue
  printf '%s\n' "$BANNER" > /etc/motd
}
validate_host() {
  python3 "$RENDER" "$1" 127.0.0.1 >/dev/null
  [[ "$1" != *.local ]] || { echo "Keine private .local-Domain als oeffentliche Audio-URL."; return 1; }
}
prepare_host() {
  get_host
  if [[ -z "$HOST" ]]; then
    printf '\nOeffentlicher DNS-Hostname fuer Alexa MP3 (ohne https://): '
    IFS= read -r HOST
    [[ -n "$HOST" ]] || { echo "Abbruch."; return 1; }
    validate_host "$HOST" || { echo 'Host ungueltig.'; return 1; }
    bash "$INSTALLER" prepare "$HOST" 127.0.0.1
    printf '%s\n' "$HOST" > "$HOSTFILE"
    chmod 0600 "$HOSTFILE"
    refresh_banner
  fi
}
enable_https() {
  [[ "$EUID" == 0 && -t 0 ]] || { echo "Root in interaktiver CT-Konsole erforderlich."; return 1; }
  get_host
  if [[ "$MODE" == shared ]]; then
    get_ip
    echo "Bestehender Nginx-Proxy CT $PROXY_CT ($PROXY_IP) bedient die Domain $HOST."
    echo "DNS-Domain zuerst auf https://www.duckdns.org registrieren und aktualisieren."
    echo "Keine Ports in der FRITZ!Box umstellen. In der Proxmox-Host-Shell:"
    printf '  pct enter %s\n' "$PROXY_CT"
    echo "Dann IM PROXY-CT:"
    printf '  certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name %s -d %s\n' "$HOST" "$HOST"
    printf '  bash /opt/tafa-audio-setup-%s/install-nginx-proxy.sh enable %s %s --shared\n' "$NEW_CT" "$HOST" "$IP"
    if [[ "$HOST" == *.duckdns.org ]]; then
      echo "Optional fuer DuckDNS-IP-Aktualisierung:"
      printf '  bash /opt/tafa-audio-setup-%s/install-duckdns-updater.sh %s\n' "$NEW_CT" "$HOST"
      echo "DuckDNS-Account-Token im Proxy-CT verdeckt eingeben, nicht im Chat."
    fi
    return 0
  fi
  prepare_host || return 1
  get_host
  tls_status
  if [[ "$HTTPS" == https://* ]]; then
    echo "HTTPS wurde bereits aktiviert: $HTTPS"
    return 0
  fi
  if [[ ! -f /etc/nginx/sites-available/tablet-assist-audio ]]; then
    echo "Nginx-Audio-Site fehlt, bitte die Installation kontrollieren."; return 1
  fi
  printf '\nVor Zertifikatsausstellung bitte sicherstellen:\n'
  printf '  - Oeffentlicher DNS-Name %s zeigt auf deine oeffentliche Anschluss-IP.\n' "$HOST"
  printf '  - TCP 80 und 443 erreichen den Nginx-CT; es existiert keine konkurrierende Weiterleitung.\n'
  printf '  - Nie 5000, 5001, 8080 oder 10300 ins Internet weiterleiten.\n'
  printf 'Diese Voraussetzungen wurden ausserhalb dieses Scripts eingerichtet? Tippe JA: '
  IFS= read -r ANSWER
  [[ "$ANSWER" == "JA" ]] || { echo "Keine Aenderung, spaeter wiederholen."; return 1; }
  certbot certonly --webroot -w /var/lib/tablet-assist-acme \
    --cert-name "$HOST" -d "$HOST"
  bash "$INSTALLER" enable "$HOST" 127.0.0.1
  refresh_banner
  echo "HTTPS ist aktiviert. In TAFA unter Alexa-Audio-URL https://$HOST eingeben."
}
run_wizard() {
  [[ "$EUID" == 0 && -t 0 ]] || { echo "Als root interaktiv im CT ausfuehren."; exit 1; }
  while true; do
    printf '\nTAFA Setup (kombinierter Sprachserver)\n'
    printf '  1) Status und Home-Assistant-Adressen anzeigen\n'
    printf '  2) Alexa HTTPS per DNS und Certbot aktivieren\n'
    printf '  3) Piper/MP3/Whisper/Nginx Service-Status anzeigen\n'
    printf '  4) Konsoleninfo aktualisieren\n'
    printf '  0) Beenden\nAuswahl: '
    IFS= read -r SELECTED
    case "$SELECTED" in
      1) show_status ;;
      2) enable_https || true ;;
      3) systemctl --no-pager --full status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio nginx || true ;;
      4) refresh_banner; echo "Konsole aktualisiert." ;;
      0) return 0 ;;
      *) echo "Bitte 0 bis 4 waehlen." ;;
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
