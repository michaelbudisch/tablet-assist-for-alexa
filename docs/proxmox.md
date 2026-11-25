# CPU-Sprachserver

[English](en/proxmox.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Voraussetzungen: aktuelles Proxmox VE oder Debian 12/13 mit systemd; für die CPU-Basis zunächst 4 vCPU, 4 GiB RAM und 20 GiB Speicher als Startgröße (abhängig vom Modell). Unterstützte Architektur und Python-Version der Abhängigkeiten prüfen. Eine NVIDIA-GPU ist nicht notwendig. Download der Modelle benötigt Internet; Laufzeit kann anschließend lokal bleiben.

**Bestehender Proxmox-Sprachserver:** Um ausschließlich den bisherigen tokenpflichtigen MP3-Generator zu aktualisieren, die aktuellen Repository-Dateien im dedizierten Debian-Gast bereitstellen und dort `sudo bash proxmox/update-mp3-generator.sh` ausführen. Das Skript sichert die vorhandene `api.py`, startet nur `jarvis-mp3.service` neu und stellt bei Fehlern die Vorgängerversion wieder her. Piper, Whisper, Audiodateien und HTTPS-Proxy bleiben unverändert. Passend dazu TAFA-Integration 0.4.3 verwenden. **Nicht auf dem Proxmox-Host ausführen.** Port 5001 niemals ins Internet weiterleiten.

## Empfohlen: ein gemeinsamer Container per Ein-Zeilen-Installer (Proxmox VE)

Für eine **Neuinstallation** genügt ein einziger Debian-LXC-Container mit Piper, Wyoming-Whisper, MP3-Generator und Nginx. **Bestehende CTs werden nicht verändert oder zusammengelegt.** Die bisherige Installation mit getrennten CTs funktioniert weiterhin.

Auf dem **Proxmox-Host**, in der interaktiven PVE-Shell als `root`, folgende Zeile ausführen:

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh && bash /root/tafa-pve-install.sh
```

**Sprache und CT-Name:** Alle Dialoge des Installers, Wiederaufnahme-Assistenten und der späteren CT-Konsole sind auf **Englisch**. Nach der Auswahl der CT-ID fragt der Installer `Container hostname [tafa-voice]` ab. Hier kannst du einen eigenen Namen eingeben (1–63 Zeichen, Kleinbuchstaben, Ziffern und Bindestriche, z. B. `jarvis-speech`, ohne führenden oder abschließenden Bindestrich). Dieser Name wird bei der Erstellung als echter Proxmox-Hostname verwendet. Eine bereits laufende Installation wird dadurch nicht nachträglich umbenannt.

**Root-Passwort direkt bei der Erstellung:** Sobald `pct create` startet, fragt Proxmox das Passwort für den Container-Benutzer `root` verdeckt ab und lässt es bestätigen. Damit funktioniert die normale CT-Konsole sofort nach der Installation. Das Passwort wird nicht in TAFA-Dateien, Argumenten oder Protokollen gespeichert. Bei CTs, die mit einer älteren Installer-Version ohne Passwort erstellt wurden, bleibt die einmalige Einrichtung über `pct enter CTID` und `passwd root` erforderlich.

Das Skript kommt aus diesem Repository. Wer es vorab ansehen möchte, öffnet `/root/tafa-pve-install.sh` vor dem Ausführen. Es führt durch die Auswahl von **freier CT-ID, Rootfs-/Template-Speicher, Netzwerk-Bridge, DHCP/statischer IP, CPU, RAM, Festplattengröße, optionalem Qwen-GPU-Worker und optionalem Alexa-Audio-Hostnamen**. Erst nach Bestätigung durch Eingabe der CT-ID wird der neue unprivilegierte Container erstellt. Standard: 4 vCPU, 4 GiB RAM, 32 GiB Disk.

Im Gast laufen Piper HTTP (5000), die interne tokenfreie MP3-API (5001), Wyoming-Whisper (10300), der temporäre MP3-Dateiserver nur auf **127.0.0.1:8080** und Nginx (80/443; HTTPS erst nach Zertifikatseinrichtung). Die bestehenden Proxmox-/Nginx-/Home-Assistant-Installationen bleiben unberührt. Das Skript installiert keine Router-Portweiterleitungen und stellt keine Zertifikate aus, bevor DNS und Erreichbarkeit vorbereitet wurden.

Die **CT-Konsole** zeigt IP, Ports und Dienst-Adressen vor dem Login unter `/etc/issue` und nach dem Login interaktiv. Die Anzeige wird beim Boot und regelmäßig aktualisiert. Im Container:

```bash
tafa-info              # Aktuelle IP, Ports und Dienste
tafa-setup             # Interaktiver Assistent für Alexa-HTTPS/Certbot
```

Falls die Proxmox-Konsole einen Root-Login verlangt und noch kein Passwort existiert: auf dem **PVE-Host** mit `pct enter CTID` in den neuen Container wechseln und dort einmal `passwd root` ausführen. Das Passwort nicht in Shell-Skripte, Chat oder Logs schreiben.

**Alexa-HTTPS:** Ein öffentlicher DNS-Hostname und gezielte Erreichbarkeit auf TCP 80/443 müssen bewusst eingerichtet werden. Anschließend `tafa-setup` *im neuen Container* starten. Es aktiviert ausschließlich einen restriktiven MP3-Dateizugriff per HTTPS. **Niemals** die internen Ports 5000/5001/8080/10300 ins Internet weiterleiten. Falls bereits ein zentraler Proxy deine Ports 80/443 verwendet, diesen erst bewusst umstellen oder den bestehenden Proxy weiterverwenden; es ist keine automatische Übernahme vorgesehen.

## Vorhandener zentraler Nginx-Proxy (Home Assistant / MCP / Alexa)

Wenn derselbe Nginx-CT bereits Home Assistant, ShapeAnywhere-MCP und die oeffentliche Alexa-Audio-Adresse bedient, **diesen CT behalten**. Die Neuinstallation mit Nginx im Sprachserver-CT ist fuer frische Umgebungen gedacht. Sie aendert bestehende CTs, DNS, Zertifikate und Routerweiterleitungen nicht.

**Wichtig:** Beim neuen Kombi-CT ist die MP3-Dateiausgabe ausschliesslich an `127.0.0.1:8080` gebunden. Ein anderer Proxy-CT kann diesen Loopback-Port **nicht** erreichen. Fuer eine bestehende Multi-Site-Installation deshalb den separaten Sprachserver-CT nutzen oder den vorhandenen Sprachserver aktualisieren. Eine spaetere Backend-Migration benoetigt eine gezielt LAN-erreichbare MP3-Ausgabe und passende Firewallregeln.

Zum vorsichtigen Aufraeumen gibt es das **nur lesende** Skript `proxmox/audit-shared-proxy.sh`. Es listet aktive Nginx-Seiten, Domains, Proxy-Ziele sowie Zertifikatsablaufdaten auf, ohne Einstellungen zu veraendern. Erst nach dem Pruefen alter Sites etwas entfernen.

## Unterbrochene Neuinstallation ohne CT-Neuerstellung fortsetzen

Wenn der neue Debian-CT bereits erstellt wurde, die Proxmox-Webkonsole aber geschlossen wurde, gibt es zwei unterstützte Wiederaufnahmepunkte: **(1) der leere neue CT, in dem noch kein TAFA installiert ist**, und **(2) nach `pip install` bei `runuser ... Permission denied`**, bevor Dienste konfiguriert wurden. Der Installer prüft den Zustand und verändert keine bereits vollständig eingerichtete TAFA-Installation.

Bei alten Installer-Versionen wurde die Python-venv mit `umask 077` angelegt. Der aktuelle Installer verwendet `umask 022` ausschließlich für die venv-Installation. Bereits geladene Pakete können dadurch erhalten bleiben.

Auf dem **Proxmox-Host** starten:

```bash
curl -fsSLo /root/tafa-resume.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/resume-install.sh && bash /root/tafa-resume.sh
```

Der Assistent fragt die CT-ID, die neue registrierte Audio-Domain, optional den GPU-Worker und den bestehenden Proxy-CT ab. Für den Fall mit einem zentralen Proxy `shared` verwenden. Er kontrolliert den Abbruchzustand und verlangt die englische Bestätigung `RESUME`; er erstellt keinen neuen CT, entfernt keine Container und ändert keine bestehenden Websites. Ist der CT noch leer, installiert er TAFA; andernfalls repariert er die unterbrochene Python-Umgebung. Dann bereitet er **eine zusätzliche** Audio-Website vor und zeigt die Certbot-/HTTPS-Befehle. Bei andersartigen Fehlern nicht blind fortsetzen.

## Neuinstallation testen, obwohl bereits ein zentraler Nginx-Proxy läuft

**Beispiel: Proxmox CT 101 bleibt für Home Assistant, ShapeAnywhere-MCP und Alexa zuständig.** So kannst du den Installer trotzdem vollständig testen, ohne 80/443 an einen anderen CT weiterzuleiten.

1. Auf [duckdns.org](https://www.duckdns.org) eine **neue, noch verfügbare Subdomain** anlegen, z. B. `tafa-neu.duckdns.org`. DuckDNS-Domains werden im Web-Dashboard registriert; die dokumentierte Update-API ändert nur den DNS-Eintrag bereits registrierter Domains. Bestehende Domainnamen behalten.
2. Im **Proxmox-Host** den Ein-Zeilen-Installer oben starten, neuen freien CT erstellen und bei **HTTPS-Modus** `shared` wählen. Danach den **bereits bestehenden Nginx-CT** angeben (z. B. `101`) und die zusätzliche Nginx-Audio-Site ausdrücklich mit `YES` bestätigen.
3. Der neue CT installiert **Piper, Whisper und MP3**, aber **keinen zweiten öffentlichen Nginx-Server**. Der alte Nginx-CT behält seine öffentlichen Portfreigaben. Der neue CT liefert MP3-Dateien auf Port 8080 ausschließlich an die IP des gewählten Proxys (zusätzliche Firewall-Einschränkungen empfohlen).
4. Der Installer kopiert die benötigten Dateien in ein **neues Verzeichnis** auf dem bestehenden Proxy und ruft dort `prepare ... --shared` auf. Dabei wird nur eine neue, streng begrenzte Audio-Site angelegt; bereits existierende Websites, Zertifikate und Routing-Regeln werden nicht überschrieben.
5. Nach erfolgter DNS-Aktualisierung auf **CT 101** das vom Installer ausgegebene `certbot certonly --webroot ...` ausführen und danach die ebenfalls ausgegebene `install-nginx-proxy.sh enable ... --shared`-Zeile. So wird das TLS-Zertifikat dort verwaltet, wo die öffentlichen Ports ankommen.
6. Optional für dynamische IPv4: Auf **CT 101** `bash /opt/tafa-audio-setup-CTID/install-duckdns-updater.sh NEUE-DOMAIN.duckdns.org` ausführen. Es fragt den **DuckDNS-Account-Token verdeckt** ab und speichert ihn ausschließlich lokal in `/etc/tafa-duckdns/` (0600); ein systemd-Timer aktualisiert nur diesen neuen DNS-Eintrag alle zehn Minuten. **Der DuckDNS-Account-Token ist kein TAFA-API-Token.** Niemals ins GitHub-Repository oder in einen Chat kopieren.
7. In einer **separaten Home-Assistant-Testinstallation** die **interne MP3-API des neuen CTs** (`http://NEUE-CT-IP:5001`) und die **neue öffentliche HTTPS-Domain** (`https://NEUE-DOMAIN.duckdns.org`) gemeinsam einstellen. Auch Piper `http://NEUE-CT-IP:5000` und Wyoming `NEUE-CT-IP:10300` auf den neuen CT setzen. Danach eine Alexa-Testdurchsage prüfen.

**Wichtig zur späteren Migration:** Eine neue Domain, die auf den neuen CT zeigt, kann **nicht** die Dateien des alten MP3-Generators ausliefern. `mp3_base` und `public_audio_base` müssen zusammen auf den neuen CT umgestellt werden; nur die Domain allein zu wechseln würde Alexa-Audio unterbrechen. Solange der Test läuft, bleibt die alte produktive HA-Installation mit dem alten CT und der alten Domain unverändert. Den bestehenden Proxy CT 101 und die übrigen Sites nicht löschen.

## Neuer separater Sprachserver-CT (Alternative)

In Proxmox eine Debian-Vorlage in der Oberfläche herunterladen. Repository auspacken/klonen. Auf dem Proxmox-Host als Administrator:

```bash
bash proxmox/create-ct.sh <freie-CT-ID> <Debian-Template-Volume> <Storage> [Bridge]
```

Das Skript fragt die CT-ID zur Bestätigung ab, erstellt nur einen neuen unprivilegierten CT (DHCP, kein Portforwarding) und installiert darin die Komponenten. Die Platzhalter ersetzen. Vorher Storage und Bridge prüfen. Für eine bereits vorhandene **leere** Debian-VM/CT stattdessen darin ausführen:

```bash
sudo bash proxmox/install-speechserver.sh
```

Das Skript verweigert die Installation auf dem PVE-Host und bei vorhandener Jarvis-Installation oder belegten Ports. Es installiert Python-Umgebung, Piper, Whisper, FFmpeg, MP3-API, temporäre Audioauslieferung, Systemd-Dienste und einen Cleanup-Timer. Es lädt eine deutsche Thorsten-Stimme herunter. Abhängigkeiten/Modelle können sich ändern; eine frische Installation ist noch nicht vollständig getestet.

## Prüfen

```bash
systemctl status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio
curl -fsS http://127.0.0.1:5001/health
journalctl -u jarvis-whisper -n 50 --no-pager
```

Die lokale Konfiguration liegt unter `/etc/jarvis-local.env` (nur root). Ab dem neuen Installer ist **kein MP3-API-Token erforderlich**. Im TAFA-Optionsbereich nur Generator-URL `http://SERVER:5001` und öffentliche HTTPS-Adresse eintragen. CPU-Host-Adresse und Port 10300 beim Wyoming-Setup angeben. Port 5001 darf ausschließlich im privaten LAN erreichbar sein.

| Port | Dienst | Zugriff |
|---|---|---|
| 5000 | Piper HTTP (WAV) | nur interne vertrauenswürdige Clients |
| 5001 | MP3-Generator | ausschließlich privates LAN, kein Token |
| 10300 | Wyoming STT | intern, kein öffentliches Netzwerk |
| 8080 | temporäre Audio-Dateien | intern; optional streng begrenzter HTTPS-Proxy |

Firewall-Regeln administrativ so setzen, dass lediglich die benötigten HA- und Proxy-Hosts zugreifen dürfen. Keine automatische Router-Konfiguration. Die GPU-Adresse bleibt zunächst leer; siehe `worker.md`.

## Optionaler HTTPS-Proxy

**Beim neuen Ein-CT-Installer ist Nginx schon integriert.** Im neuen Container `tafa-setup` verwenden, sobald der DNS-Name und der bewusste HTTPS-Zugriff vorbereitet sind. Die getrennte Proxy-CT-Installation gemäß [Anleitung](nginx-proxy.md) bleibt als Alternative für vorhandene Umgebungen erhalten. Für reines Tablet/Echo-Bluetooth ist kein öffentlicher Audio-Proxy nötig.
