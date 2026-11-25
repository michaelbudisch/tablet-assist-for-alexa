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

Das Skript kommt aus diesem Repository. Wer es vorab ansehen möchte, öffnet `/root/tafa-pve-install.sh` vor dem Ausführen. Es führt durch die Auswahl von **freier CT-ID, Rootfs-/Template-Speicher, Netzwerk-Bridge, DHCP/statischer IP, CPU, RAM, Festplattengröße, optionalem Qwen-GPU-Worker und optionalem Alexa-Audio-Hostnamen**. Erst nach Bestätigung durch Eingabe der CT-ID wird der neue unprivilegierte Container erstellt. Standard: 4 vCPU, 4 GiB RAM, 32 GiB Disk.

Im Gast laufen Piper HTTP (5000), die interne tokenfreie MP3-API (5001), Wyoming-Whisper (10300), der temporäre MP3-Dateiserver nur auf **127.0.0.1:8080** und Nginx (80/443; HTTPS erst nach Zertifikatseinrichtung). Die bestehenden Proxmox-/Nginx-/Home-Assistant-Installationen bleiben unberührt. Das Skript installiert keine Router-Portweiterleitungen und stellt keine Zertifikate aus, bevor DNS und Erreichbarkeit vorbereitet wurden.

Die **CT-Konsole** zeigt IP, Ports und Dienst-Adressen vor dem Login unter `/etc/issue` und nach dem Login interaktiv. Die Anzeige wird beim Boot und regelmäßig aktualisiert. Im Container:

```bash
tafa-info              # Aktuelle IP, Ports und Dienste
tafa-setup             # Interaktiver Assistent für Alexa-HTTPS/Certbot
```

Falls die Proxmox-Konsole einen Root-Login verlangt und noch kein Passwort existiert: auf dem **PVE-Host** mit `pct enter CTID` in den neuen Container wechseln und dort einmal `passwd root` ausführen. Das Passwort nicht in Shell-Skripte, Chat oder Logs schreiben.

**Alexa-HTTPS:** Ein öffentlicher DNS-Hostname und gezielte Erreichbarkeit auf TCP 80/443 müssen bewusst eingerichtet werden. Anschließend `tafa-setup` *im neuen Container* starten. Es aktiviert ausschließlich einen restriktiven MP3-Dateizugriff per HTTPS. **Niemals** die internen Ports 5000/5001/8080/10300 ins Internet weiterleiten. Falls bereits ein zentraler Proxy deine Ports 80/443 verwendet, diesen erst bewusst umstellen oder den bestehenden Proxy weiterverwenden; es ist keine automatische Übernahme vorgesehen.

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
