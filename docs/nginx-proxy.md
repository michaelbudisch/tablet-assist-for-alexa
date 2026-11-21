**Deutsch** | [English](en/nginx-proxy.md) · [Projektübersicht](../README.de.md)

# Optional: Nginx-Proxy-CT für Alexa-Durchsagen

**Nur für die optionale Alexa-MP3-Ausgabe notwendig.** Native Assist-Antworten über die Bluetooth-Verbindung Tablet → Echo benötigen keine öffentliche Audio-URL. Der Proxy stellt keine Sprachgenerierungs-API bereit.

## Voraussetzungen

Ein neuer Debian-CT auf Proxmox, eine freie CT-ID, der bestehende CPU-Sprachserver mit internem Port 8080, ein eigener öffentlicher DNS-Name und ein gültiges öffentlich vertrauenswürdiges TLS-Zertifikat. Für Let's Encrypt HTTP-01 müssen öffentliche DNS-Auflösung und TCP 80 funktionieren, für Alexa TCP 443. Bei CGNAT, DS-Lite oder einem vorhandenen Reverse Proxy die tatsächliche Netzarchitektur prüfen; keine konkurrierenden Portweiterleitungen. Intern ausschließlich dem Proxy den benötigten Zugriff auf Port 8080 erlauben; HA und die übrigen Sprach-/GPU-Dienste bleiben im vertrauenswürdigen LAN. DNS und Router werden nicht automatisiert verändert.

## DuckDNS über die Home Assistant App (optional)

Bei einem dynamischen Internetanschluss kann die offizielle **Duck DNS App** in HA die öffentliche IP-Adresse automatisch aktualisieren. Certbot auf dem Proxy bleibt separat für die Zertifikate zuständig.

1. Bei DuckDNS einen eigenen Audio-Subdomainnamen registrieren (Beispiel: `my-assist-audio.duckdns.org`; nicht die Beispieladresse verwenden).
2. In Home Assistant unter Einstellungen → Apps → App installieren die offizielle **Duck DNS** App auswählen. In ihrer Konfiguration den eigenen Namen zur bestehenden Domainliste hinzufügen; bestehende Domains beibehalten. Den DuckDNS-Token ausschließlich in der lokalen App-Konfiguration hinterlegen.
3. Wenn die App nur DNS aktualisieren soll und Certbot alle Zertifikate auf dem Proxy verwaltet, kann `lets_encrypt.accept_terms: false` eingestellt werden. Bei einer bestehenden Installation mit von der App verwalteten Zertifikaten diese Einstellung nicht ohne Prüfung ändern. Beide Dienste nicht für dasselbe Zertifikat konfigurieren.
4. App starten und Protokoll bzw. DNS-Auflösung prüfen. Bei IPv6 prüfen, dass auch ein vorhandener AAAA-Eintrag auf den richtigen öffentlichen Proxy verweist. DNS-Aktualisierung ist keine Bestätigung der externen Erreichbarkeit.

Offizielle [Duck DNS App-Dokumentation](https://github.com/home-assistant/apps/blob/master/duckdns/DOCS.md). Alternativ jeder andere DNS-Anbieter. Der Proxy benötigt keinen DuckDNS-Token; der Sprachserver benötigt keine öffentliche IP.

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

## Alternative: bestehenden Nginx-Proxy-CT nutzen

Wer bereits einen Proxy mit funktionierenden TLS-Webseiten betreibt, braucht keinen weiteren CT und keine zusätzliche Weiterleitung am Router. Mehrere Domains können über denselben Proxy laufen. Für einen **neuen, bisher unbenutzten Audio-Hostnamen** im bestehenden Debian-CT mit installiertem Nginx und Certbot das Repository klonen, Konfiguration und Zertifikate lokal sichern und ausführen:

```bash
bash proxmox/install-nginx-proxy.sh prepare PUBLIC_HOST SPEECHSERVER_HOST --shared
certbot certonly --webroot -w /var/lib/tablet-assist-acme --cert-name PUBLIC_HOST -d PUBLIC_HOST
bash proxmox/install-nginx-proxy.sh enable PUBLIC_HOST SPEECHSERVER_HOST --shared
certbot renew --cert-name PUBLIC_HOST --dry-run
```

Der Installer fügt ausschließlich eine eigene Site hinzu. Vorhandene vHosts, Default-Site und Certbot-Timer bleiben unverändert. Er bricht bei bereits verwendeten exakten Hostnamen oder dem vorhandenen Ziel-Dateinamen ab. Wildcard- und Regex-Servernamen sowie vorhandene Zertifikate vorher manuell prüfen. Bestehende Audio-vHosts (auch Certbot-`--nginx`-Installationen) **nicht** mit diesem Skript ersetzen; ihre bisherige Zertifikatsmethode beibehalten. Die Konfiguration eines vorhandenen Audio-vHosts kann lokal mit der neu erzeugten Vorlage verglichen werden:

```bash
python3 proxmox/render-nginx-proxy.py PUBLIC_HOST SPEECHSERVER_HOST --tls
```

Der Produktionsproxy wird erst nach erfolgreichem `nginx -t` neu geladen. Bestehende Certbot-Erneuerung kontrollieren (z. B. `systemctl list-timers --all` und `certbot certificates`). Ein neuer Webroot-Deploy-Hook lädt Nginx nach Erneuerung neu. Bestehende Certbot-Konfigurationen niemals pauschal umstellen. Bei abweichendem Nginx-Verzeichnislayout manuelle Installation nutzen.

## 3. Sicherheitsgrenzen

- Nur GET/HEAD für genau 32-stellige Hex-Dateinamen plus .mp3 über HTTPS, keine API, keine Dateiliste. Andere Pfade werden abgewiesen; HTTP dient nur ACME.
- Upstream ausschließlich der Audio-Port 8080. Keine Veröffentlichung von 5000, 5001, 10300, GPU, Proxmox oder HA.
- Die MP3-Links sind zufällig und 15 Minuten abrufbar; kein Login. Dritte mit Link können sie währenddessen abrufen. Keine vertraulichen Inhalte. Cache-Control no-store, Zugriff-Logging deaktiviert, Ratenbegrenzung. Sprachserver löscht die Audiodateien separat. Alexa verarbeitet die Nachricht als Cloud-Dienst.
- Standardmäßig nur für einen dedizierten CT; für einen vorhandenen Debian-Proxy nur den ausdrücklich beschriebenen Zusatzmodus `--shared` für einen neuen Hostnamen verwenden. Bestehende vHosts nicht automatisch ändern.

## 4. Prüfung

```bash
nginx -t
systemctl status nginx certbot.timer
curl -I https://PUBLIC_HOST/health
curl -I https://PUBLIC_HOST/generate
curl -I https://PUBLIC_HOST/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.mp3
```

Die drei Beispielpfade sollen 404 ergeben, sofern die Beispieldatei nicht existiert. Eine selbst erzeugte nicht vertrauliche MP3-URL zusätzlich von außerhalb des Heimnetzes testen: HTTP 200 und audio/mpeg vor Ablauf, 404 nach Ablauf. Keine Generierungs-API öffentlich testen oder freigeben.

In HA die interne MP3-API-Adresse (Port 5001), den lokal gespeicherten API-Schlüssel und den öffentlichen HTTPS-Ursprung ohne Pfad setzen. Siehe [Marketplace](marketplace.md). Bei bereits funktionierender Installation des Audio-vHosts ist kein Umbau nötig. Die neue Vorlage erlaubt ausschließlich zufällige MP3-Dateinamen; eine dauerhaft erreichbare test.mp3 ist bewusst nicht enthalten. Einen eigenen kurzlebigen Testclip über den internen Sprachserver erzeugen.
