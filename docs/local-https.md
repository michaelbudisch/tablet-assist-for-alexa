# Optional: lokales HTTPS für TAFA mit vorhandenem NGINX

[English](en/local-https.md) | **Deutsch** · [Projekt](../README.de.md)

Für das TAFA-Mikrofon im Browser/Android-WebView wird ein **vertrauenswürdiger HTTPS-Ursprung** benötigt. Mit *Split-DNS* benutzt das Tablet den **bestehenden** HTTPS-Hostnamen und das vorhandene Zertifikat, verbindet sich im WLAN aber mit der **lokalen IP des NGINX-Proxys**. Kein zusätzlicher NGINX auf HA und keine weiteren Router-Portfreigaben nötig.

```text
Tablet -> https://ha.example.org
        -> lokaler DNS: ha.example.org = 192.168.1.20
        -> bestehender NGINX/Certbot (192.168.1.20:443)
        -> lokaler Home Assistant (192.168.1.30:80 oder :8123)
```

Die Domain muss bereits als NGINX-`server_name` mit **gültigem HTTPS-Zertifikat und funktionierender HA-/WebSocket-Weiterleitung** eingerichtet sein. Alle Adressen sind Platzhalter. Bestehende MCP- und Alexa-MP3-Domains bleiben unberührt.

## DNS auf einem bestehenden Debian-/Proxmox-NGINX-Gast

Repository im **NGINX-Gast/CT**, nicht auf dem Proxmox-Host, klonen. Bei freiem TCP-/UDP-Port 53:

```bash
sudo bash proxmox/install-local-https-dns.sh install ha.example.org 192.168.1.20 192.168.1.1
```

Parameter: **HTTPS-Hostname**, **LAN-IP des NGINX-Proxys (nicht HA!)**, **Router-/DNS-IP**. Das Skript validiert die Adressen, verweigert bestehende DNS-Installationen/Portkonflikte, verwaltet nur `/etc/dnsmasq.d/tafa-local-https.conf` und startet dnsmasq. Es **verändert keine NGINX-Sites, HA-Konfigurationen, Zertifikate oder Routerfreigaben**. DNS-Port 53 niemals im Internet freigeben; nur vertrauenswürdigen LAN-Clients erlauben.

Läuft bereits dnsmasq, AdGuard oder Pi-hole? **Den Installer nicht verwenden.** Stattdessen im vorhandenen DNS einen lokalen Host-Eintrag `ha.example.org -> 192.168.1.20` anlegen. Bestehende Konfigurationen vor Änderungen sichern.

Voransicht ohne Installation:

```bash
python3 proxmox/render-local-https-dns.py ha.example.org 192.168.1.20 192.168.1.1
```

## Zuerst testen

```bash
nslookup ha.example.org 192.168.1.20
curl -sS --max-time 8 --resolve ha.example.org:443:192.168.1.20 \
  -o /dev/null -w 'HTTPS: %{http_code} | Zertifikat: %{ssl_verify_result}\n' \
  https://ha.example.org/
```

Erwartet: DNS antwortet mit **192.168.1.20**, Zertifikatsprüfung **0**, HA üblicherweise mit HTTP **200**. **Kein `-k`**, damit Zertifikatsprobleme sichtbar bleiben. `curl -I` kann auf HA bei HEAD-Anfragen `405` ergeben.

## Android-Tablet / Companion-App

1. Tablet-WLAN-IP, Gateway und Präfix notieren; möglichst DHCP-Reservierung im Router einrichten.
2. **WLAN → verbundenes Netzwerk → Erweitert → IP-Einstellungen → Statisch**. Bisherige IP, Gateway und Präfix übernehmen.
3. **DNS 1** auf die **Proxy-LAN-IP** setzen (Beispiel `192.168.1.20`), nicht auf die Home-Assistant-IP. Falls DNS 2 erforderlich ist, ebenfalls lokalen DNS statt `8.8.8.8` verwenden.
4. Android **Privates DNS** zum Test auf **Aus** stellen. Browser-DoH und IPv6-DNS/AAAA können lokale Auflösung umgehen; bei Problemen prüfen.
5. WLAN neu verbinden und `https://ha.example.org` in Chrome **ohne Zertifikatswarnung** testen. Companion-App: denselben HTTPS-Hostnamen als **interne URL** und die Heim-WLAN-SSID eintragen, nötige WLAN-/Standortberechtigungen erteilen und App neu starten. WebSocket und Mikrofon testen.

**Nie `https://192.168.1.20` als HTTPS-Adresse benutzen:** Das Zertifikat gilt für den Hostnamen, nicht die numerische LAN-IP. Andere Heimnetzgeräte müssen ihren DNS nicht ändern.

## Offlinebetrieb, Sicherheit, Rückbau

Lokales DNS und HTTPS bleiben bei Internetausfall verfügbar, solange Proxy, WLAN und HA laufen. Lokale STT/TTS/LLMs können weiterarbeiten; Alexa, Cloud-KI, Fernzugriff und spätere Zertifikatserneuerung benötigen Internet. Ein gültiges Zertifikat bleibt bis zum Ablaufdatum gültig.

**Split-DNS macht eine öffentlich weitergeleitete HA-Oberfläche nicht privat.** Öffentliche NGINX-Routen bleiben erreichbar; diese separat mit starkem Passwort, MFA und geprüften Regeln schützen. MCP-/OAuth-Endpunkte nicht ungetestet sperren. DNS-Port 53 nicht ins Internet öffnen.

- **403:** DNS zeigt noch öffentlich oder NGINX-Zugriffsbeschränkung greift; IP, IPv6, Privates DNS/DoH prüfen.
- **DNS-Timeout:** `systemctl status dnsmasq`, TCP/UDP 53 und Firewall prüfen.
- **502:** NGINX-Backend-Port und HA-Trusted-Proxy-Einstellung prüfen.
- **Mikrofon/Zertifikat:** HTTPS-Hostnamen, Zertifikatsgültigkeit, Android-Berechtigungen prüfen; Warnungen nie umgehen.

```bash
sudo bash proxmox/install-local-https-dns.sh remove
```

Danach Tablet-IP-Einstellungen auf **DHCP** und Privates DNS auf die vorherige Einstellung zurücksetzen. Der Rückbau ändert weder NGINX noch Zertifikate. [NGINX-Proxy](nginx-proxy.md) · [Multiroom](../homeassistant/examples/MULTIROOM.de.md) · [Sicherheit](security.md).
