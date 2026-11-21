[Deutsch](../nginx-proxy.md) | **English** · [Project overview](../../README.md)

# Optional Nginx proxy container for Alexa announcements

**Only required for optional Alexa MP3 playback.** Native Assist responses played through a tablet-to-Echo Bluetooth connection do not require a public audio URL. Never publish the speech generation API.

## Requirements

A new Debian CT on Proxmox, an unused CT ID, the CPU speech server with internal port 8080, a public DNS hostname and a publicly trusted TLS certificate. Let's Encrypt HTTP-01 requires public DNS resolution and TCP 80; Alexa needs TCP 443. For CGNAT, DS-Lite or an existing reverse proxy, check the actual network architecture before proceeding. Do not create conflicting port forwards. Internally, allow only the proxy's required access to port 8080. HA and other speech/GPU services stay on the trusted LAN. The scripts do not change DNS or router settings.

## DuckDNS via the Home Assistant app (optional)

For dynamic Internet connections, the official Duck DNS app can keep the public IP up to date. Certbot on the proxy remains responsible for certificates.

1. Register your own DuckDNS audio subdomain (example: `my-assist-audio.duckdns.org`; use your own name).
2. In HA, open Settings → Apps → Install app and select the official Duck DNS app. Add your audio hostname to its existing domain list without removing configured names. Store the DuckDNS token only in the local app configuration.
3. If the app only updates DNS and all certificates are managed by Certbot on the proxy, use `lets_encrypt.accept_terms: false`. Do not change this without checking an existing app-managed certificate setup. Do not configure both services to manage the same certificate.
4. Start the app and check its log and DNS resolution. If using IPv6, ensure any AAAA record points to the correct public proxy. A DNS update on its own does not establish external reachability.

[Official Duck DNS app documentation](https://github.com/home-assistant/apps/blob/master/duckdns/DOCS.md). Other DNS providers can also be used. Neither the proxy nor the speech server needs the DuckDNS token, and the speech server does not need a public IP.

## 1. Create a container

Clone the repository on Proxmox. On the Proxmox host:

```bash
bash proxmox/create-proxy-ct.sh CTID TEMPLATE_VOLUME STORAGE PUBLIC_HOST SPEECHSERVER_HOST [BRIDGE]
```

Replace the placeholders and confirm the unused CT ID. The script creates an unprivileged DHCP container (1 vCPU, 512 MiB RAM, 4 GiB disk), installs Debian Nginx and Certbot, and prepares only the HTTP ACME challenge route. Set a DHCP reservation. Existing guests are not overwritten.

Alternatively, inside a new empty Debian CT with the repository cloned:

```bash
bash proxmox/install-nginx-proxy.sh prepare PUBLIC_HOST SPEECHSERVER_HOST
```

## 2. Create the certificate and enable HTTPS

Configure DNS and targeted port routing administratively beforehand. DNS-01 is an alternative; if a certificate is managed externally, provide it at the expected location. Keep DNS API keys out of Git and chat. For HTTP-01 inside the proxy CT:

```bash
certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name PUBLIC_HOST -d PUBLIC_HOST
bash /opt/tablet-assist-proxy/install-nginx-proxy.sh enable PUBLIC_HOST SPEECHSERVER_HOST
certbot renew --dry-run
```

For a manually installed guest, use the repository path. Certbot may request an email address and agreement to its terms. HTTPS is enabled only if certificate files exist and the Nginx configuration test succeeds. A renewal timer and reload hook are installed.

## Alternative: reuse an existing Nginx proxy CT

If you already have a working TLS reverse proxy, no additional CT or router forwarding is necessary. For a **new, unused audio hostname** on an existing Debian proxy with Nginx and Certbot installed, clone the repository, back up configuration and certificates locally, then run:

```bash
bash proxmox/install-nginx-proxy.sh prepare PUBLIC_HOST SPEECHSERVER_HOST --shared
certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name PUBLIC_HOST -d PUBLIC_HOST
bash proxmox/install-nginx-proxy.sh enable PUBLIC_HOST SPEECHSERVER_HOST --shared
certbot renew --cert-name PUBLIC_HOST --dry-run
```

The installer adds its own site; existing virtual hosts, default site and Certbot scheduling remain unchanged. It refuses an already configured exact hostname or existing destination file. Review wildcard/regex server names and certificates manually. **Do not replace existing audio vhosts** (including Certbot --nginx installations) with this script; preserve their existing renewal method. Compare an existing configuration locally with the generated template if needed:

```bash
python3 proxmox/render-nginx-proxy.py PUBLIC_HOST SPEECHSERVER_HOST --tls
```

Nginx is reloaded only after a successful configuration test. Check existing renewal scheduling with `systemctl list-timers --all` and `certbot certificates`. A new webroot deployment hook reloads Nginx on renewal. Do not globally change existing Certbot configurations. For nonstandard Nginx layouts, use manual configuration.

## 3. Security boundaries

- HTTPS GET/HEAD only for 32-character hexadecimal filenames ending in .mp3. No API, directory listing or other routes. HTTP serves only ACME challenges.
- The only upstream is audio port 8080. Never publish ports 5000, 5001, 10300, GPU services, Proxmox or HA through this site.
- Random MP3 URLs remain accessible for 15 minutes, without a login. Anyone who obtains a link can access the file during that time. Do not send confidential content. Cache-Control no-store, access logging disabled and rate limiting enabled. The speech server deletes expired audio independently. Alexa processes the announcement as a cloud service.
- The default installer is for a dedicated CT; use explicit `--shared` mode only for a new hostname on an existing Debian proxy. Existing vhosts are not edited automatically.

## 4. Verify

```bash
nginx -t
systemctl status nginx certbot.timer
curl -I https://PUBLIC_HOST/health
curl -I https://PUBLIC_HOST/generate
curl -I https://PUBLIC_HOST/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.mp3
```

All three paths should return 404, assuming the sample file does not exist. Verify an actual newly generated non-confidential MP3 URL from outside the LAN: HTTP 200 with audio/mpeg before expiry, 404 afterwards. Never expose or test the generation API publicly.

In HA configure the internal MP3 API (port 5001), local API key and public HTTPS origin without a path; see [Marketplace](marketplace.md). A working existing audio vhost does not need to be migrated. The new template deliberately omits a permanent test.mp3 route; generate a short-lived test clip using the internal speech server.
