#!/usr/bin/env bash
# Read-only inventory of an existing multi-site Debian Nginx proxy CT.
# Does not touch DNS, router, sites, services, certificates or HA.
set -Eeuo pipefail
export LC_ALL=C
[[ -d /etc/nginx/sites-enabled ]] || { echo "No Nginx sites-enabled directory"; exit 1; }
echo "TAFA shared Nginx proxy - read-only audit"
echo "=========================================="
echo "Enabled sites (routing declarations only):"
for site in /etc/nginx/sites-enabled/*; do
  [[ -e "$site" || -L "$site" ]] || continue
  printf '\n  %s' "$(basename -- "$site")"
  if [[ -L "$site" ]]; then printf ' -> %s' "$(readlink -- "$site")"; fi
  printf '\n'
  target="$(readlink -f -- "$site" 2>/dev/null || true)"
  if [[ -n "$target" && -f "$target" && -r "$target" ]]; then
    awk '
      /^[[:space:]]*server_name[[:space:]]/ {
        sub(/[;#].*$/, ""); gsub(/^[[:space:]]+/, ""); print "    " $0
      }
      /^[[:space:]]*listen[[:space:]]/ {
        sub(/[;#].*$/, ""); gsub(/^[[:space:]]+/, ""); print "    " $0
      }
      /^[[:space:]]*proxy_pass[[:space:]]/ {
        sub(/[;#].*$/, ""); gsub(/^[[:space:]]+/, "");
        if (match($0, /https?:\/\//)) {
          v=substr($0,RSTART);
          sub(/[?#].*$/, "", v);
          sub(/^https?:\/\/[^@/]*@/, "https://[redacted]@", v);
          sub(/\/.*$/, "", v);
          print "    proxy_pass " v
        } else print "    proxy_pass [dynamic/variable]"
      }
    ' "$target"
  else
    echo "    Site target missing or unreadable"
  fi
done
echo
echo "Nginx configuration syntax:"
if command -v nginx >/dev/null; then nginx -t 2>&1 || true; fi
echo
echo "Nginx service:"
if command -v systemctl >/dev/null; then systemctl is-active nginx 2>/dev/null || true; fi
echo
echo "Certificate metadata (never certificate private keys):"
if command -v certbot >/dev/null; then
  certbot certificates 2>&1 | grep -E 'Certificate Name:|Domains:|Expiry Date:' || true
else
  echo "Certbot not found"
fi
echo
echo "Listening TCP 80/443:"
if command -v ss >/dev/null; then
  ss -ltnH | awk '$4 ~ /:(80|443)$/ {print "  " $4}'
fi
echo
echo "No settings have been changed."
