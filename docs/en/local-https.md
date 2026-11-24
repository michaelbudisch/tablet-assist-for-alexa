# Optional: local HTTPS for TAFA using an existing NGINX proxy

**English** | [Deutsch](../local-https.md) · [Project](../../README.md)

The TAFA browser/Android WebView microphone needs a **trusted HTTPS origin**. With *split DNS*, the tablet uses the **existing HTTPS hostname and certificate** but resolves it to the **LAN IP of the existing NGINX reverse proxy** on home Wi-Fi. No second HA NGINX and no new router port forwarding.

```text
Tablet -> https://ha.example.org
       -> LAN DNS: ha.example.org = 192.168.1.20
       -> existing NGINX/Certbot (192.168.1.20:443)
       -> LAN Home Assistant (192.168.1.30:80 or :8123)
```

The hostname must already be a working HTTPS NGINX `server_name` with a **trusted certificate and HA/WebSocket forwarding**. All addresses are examples. Existing Alexa MP3 and MCP hostnames are untouched.

## DNS in an existing Debian/Proxmox NGINX guest

Clone this repo **inside the NGINX guest/CT**, not on the Proxmox host. If TCP/UDP port 53 is free:

```bash
sudo bash proxmox/install-local-https-dns.sh install ha.example.org 192.168.1.20 192.168.1.1
```

Arguments: **HTTPS hostname**, **NGINX proxy's LAN IP (not HA!)**, **existing router/DNS IP**. The script validates addresses, refuses pre-existing DNS installations/port conflicts, manages only `/etc/dnsmasq.d/tafa-local-https.conf` and starts dnsmasq. It **does not change NGINX sites, HA settings, certificates or router ports**. Never expose DNS port 53 to the Internet; restrict it to trusted LAN clients.

Already using dnsmasq, AdGuard or Pi-hole? **Do not run this installer.** Add a host override `ha.example.org -> 192.168.1.20` to the existing DNS instead. Back up existing configuration before changes.

Preview without installation:

```bash
python3 proxmox/render-local-https-dns.py ha.example.org 192.168.1.20 192.168.1.1
```

## Verify first

```bash
nslookup ha.example.org 192.168.1.20
curl -sS --max-time 8 --resolve ha.example.org:443:192.168.1.20 \
  -o /dev/null -w 'HTTPS: %{http_code} | Certificate: %{ssl_verify_result}\n' \
  https://ha.example.org/
```

Expected: DNS **192.168.1.20**, certificate verification **0**, HA usually HTTP **200**. Do **not** use `-k`, which hides TLS errors. `curl -I`/HEAD can produce an unrelated `405` on HA.

## Android tablet / Companion app

1. Record the tablet's current Wi-Fi IP, gateway and prefix; reserve the IP in the router's DHCP settings if possible.
2. **Wi-Fi → connected network → Advanced → IP settings → Static**. Keep the existing IP, gateway and prefix.
3. Set **DNS 1** to the **proxy LAN IP** (`192.168.1.20` in the example), not the Home Assistant IP. If DNS 2 is required, use the same local DNS rather than `8.8.8.8`.
4. Set Android **Private DNS** to **Off** for testing. Browser DoH and IPv6 DNS/AAAA can bypass local DNS; check these if needed.
5. Reconnect Wi-Fi; open `https://ha.example.org` in Chrome **without a certificate warning**. Set the **Companion app internal URL** to the same HTTPS hostname and select your home Wi-Fi SSID; grant required Wi-Fi/location permissions. Restart the app and test WebSockets and microphone.

**Never use `https://192.168.1.20` as the HTTPS URL:** the certificate covers the hostname, not the numeric LAN IP. Other LAN clients do not need to change DNS.

## Offline, security and rollback

LAN DNS and HTTPS remain available during a WAN outage while proxy, Wi-Fi and HA stay up. Local STT/TTS/LLMs may work; Alexa, cloud AI, remote access and future certificate renewal still require Internet. An existing trusted certificate remains valid until expiration.

**Split DNS does not make a publicly forwarded HA site private.** Public NGINX routes remain accessible; secure them separately with a strong password, MFA and tested rules. Do not blindly block MCP/OAuth endpoints. Never forward DNS port 53 publicly.

- **403:** Public DNS is still used or an NGINX access rule blocks the path; check IP, IPv6, Private DNS and DoH.
- **DNS timeout:** `systemctl status dnsmasq`, TCP/UDP 53 and firewall.
- **502:** NGINX HA backend port and HA trusted proxy configuration.
- **Mic/TLS warning:** correct HTTPS hostname, certificate validity and Android permissions; never bypass warnings.

```bash
sudo bash proxmox/install-local-https-dns.sh remove
```

Restore tablet Wi-Fi to **DHCP** and its previous Private DNS setting. Removal does not affect NGINX sites or certificates. [NGINX proxy](nginx-proxy.md) · [Multiroom](../../homeassistant/examples/MULTIROOM.md) · [Security](security.md).
