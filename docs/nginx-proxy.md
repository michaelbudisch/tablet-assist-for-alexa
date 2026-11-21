# Optional: Nginx-Proxy-CT für Alexa-Durchsagen

**Nur für die optionale Alexa-MP3-Ausgabe notwendig.** Native Assist-Antworten über die Bluetooth-Verbindung Tablet → Echo benötigen keine öffentliche Audio-URL. Der Proxy stellt keine Sprachgenerierungs-API bereit.

## Voraussetzungen

Ein neuer Debian-CT auf Proxmox, eine freie CT-ID, der bestehende CPU-Sprachserver mit internem Port 8080, ein eigener öffentlicher DNS-Name und ein gültiges öffentlich vertrauenswürdiges TLS-Zertifikat. Für Let's Encrypt HTTP-01 müssen öffentliche DNS-Auflösung und TCP 80 funktionieren, für Alexa TCP 443. Bei CGNAT, DS-Lite oder einem vorhandenen Reverse Proxy die tatsächliche Netzarchitektur prüfen; keine konkurrierenden Portweiterleitungen. Intern ausschließlich dem Proxy den benötigten Zugriff auf Port 8080 erlauben; HA und die übrigen Sprach-/GPU-Dienste bleiben im vertrauenswürdigen LAN. DNS und Router werden nicht automatisiert verändert.

## 1. CT erstellen

Repository auf Proxmox klonen. Im Proxmox-Host:

```bash
bash proxmox/create-proxy-ct.sh CTID TEMPLATE_VOLUME STORAGE PUBLIC_HOST SPEECHSERVER_HOST [BRIDGE]
```

Platzhalter ersetzen; die freie ID wird zur Bestätigung abgefragt. Ein unprivilegierter CT (1 vCPU, 512 MiB RAM, 4 GiB, DHCP) wird erstellt. Debian-Nginx und Certbot werden installiert, zunächst nur die HTTP-Route für ACME vorbereitet. DHCP-Reservierung setzen. Bestehende Gäste werden nicht überschrieben.

Alternativ im neuen leeren Debian-CT mit geklontem Repository:

```bash
bash proxmox/install-nginx-proxy.sh prepare PUBLIC_HOST SPEECHSERVER_HOST
```

## 2. Zertifikat und HTTPS aktivieren

DNS und gezielte Portfreigaben vorher administrativ einrichten. DNS-01 ist eine mögliche Alternative; bei externer Zertifikatsverwaltung Zertifikate am erwarteten Pfad bereitstellen. Keine DNS-API-Schlüssel in Git oder Chat teilen. Für HTTP-01 im Proxy-CT:

```bash
certbot certonly --webroot -w /var/lib/tablet-assist-acme -d PUBLIC_HOST
bash /opt/tablet-assist-proxy/install-nginx-proxy.sh enable PUBLIC_HOST SPEECHSERVER_HOST
certbot renew --dry-run
```

Bei manueller Gastinstallation den Repository-Pfad verwenden. Certbot fragt ggf. nach E-Mail und Zustimmung. Das Skript aktiviert HTTPS erst mit Zertifikatsdateien und erfolgreichem nginx-Test; Erneuerungstimer und Reload-Hook werden eingerichtet.

## 3. Sicherheitsgrenzen

- Nur GET/HEAD für genau 32-stellige Hex-Dateinamen plus .mp3 über HTTPS, keine API, keine Dateiliste. Andere Pfade werden abgewiesen; HTTP dient nur ACME.
- Upstream ausschließlich der Audio-Port 8080. Keine Veröffentlichung von 5000, 5001, 10300, GPU, Proxmox oder HA.
- Die MP3-Links sind zufällig und 15 Minuten abrufbar; kein Login. Dritte mit Link können sie währenddessen abrufen. Keine vertraulichen Inhalte. Cache-Control no-store, Zugriff-Logging deaktiviert, Ratenbegrenzung. Sprachserver löscht die Audiodateien separat. Alexa verarbeitet die Nachricht als Cloud-Dienst.
- Nur für einen dedizierten CT, nicht ungeprüft auf einem bestehenden Mehrzweck-Proxy verwenden.

## 4. Prüfung

```bash
nginx -t
systemctl status nginx certbot.timer
curl -I https://PUBLIC_HOST/health
curl -I https://PUBLIC_HOST/generate
curl -I https://PUBLIC_HOST/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.mp3
```

Die drei Beispielpfade sollen 404 ergeben, sofern die Beispieldatei nicht existiert. Eine selbst erzeugte nicht vertrauliche MP3-URL zusätzlich von außerhalb des Heimnetzes testen: HTTP 200 und audio/mpeg vor Ablauf, 404 nach Ablauf. Keine Generierungs-API öffentlich testen oder freigeben.

In HA die interne MP3-API-Adresse (Port 5001), den lokal gespeicherten API-Schlüssel und den öffentlichen HTTPS-Ursprung ohne Pfad setzen. Siehe [Marketplace](marketplace.md). Bei einer bestehenden Installation kann statt eines neuen CT eine passende sichere Nginx-Weiterleitung manuell übernommen werden.
