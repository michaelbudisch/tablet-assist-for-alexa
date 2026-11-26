# Optionaler CPU-Sprachserver auf Proxmox

[English](en/proxmox.md) · [Projektübersicht](../README.de.md) · [Einrichtung](setup-guide.md)

**Nicht für jede TAFA-Installation notwendig:** Die TAFA-App kann Piper und Faster-Whisper direkt lokal ausführen. Diese Anleitung richtet sich an Installationen, die die CPU-Dienste in einen separaten **Debian-LXC auf Proxmox VE** auslagern möchten. Das **Alexa-HTTPS-Gateway** für MP3-Durchsagen ist eine zusätzliche, getrennte Option. Normale Bluetooth-Antworten benötigen es nicht.

## Empfohlen: neuer kombinierter LXC

Auf dem **Proxmox-Host** in einer interaktiven Root-Shell:

```bash
curl -fsSLo /root/tafa-pve-install.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/quick-install.sh
bash /root/tafa-pve-install.sh
```

Den heruntergeladenen Installer vor der Ausführung prüfen. Der englische Assistent fragt nach **freier CT-ID**, eigenem **Container-Namen**, Speicherort/Template, Netzwerk, Ressourcen und optionaler GPU-Adresse und Alexa-Domain. Standardressourcen: **4 vCPU, 4 GiB RAM, 32 GiB Speicher**. Er erstellt nach ausdrücklicher Bestätigung einen **neuen** CT und lässt während der Erstellung das Root-Passwort setzen. **Kein Installer auf einem bestehenden Produktiv-CT ausführen.**

Die Installation stellt folgende LAN-Dienste bereit:

| Port | Verwendung | Internetzugriff |
| --- | --- | --- |
| `5000` | Piper HTTP/TTS | **Nein** |
| `10300` | Wyoming Whisper/STT | **Nein** |
| `5001` | MP3-Generator für optionale Alexa-Nachrichten | **Nein** |
| `8080` | Kurzlebige MP3-Dateien, intern für einen Proxy | **Nein – nur über freigegebenen HTTPS-Dateizugriff** |

Im **neuen CT** zeigt `tafa-info` die Dienste an. Über `tafa-setup` wird ein optionaler eigener HTTPS-Audiohost konfiguriert, sobald DNS, Ports und Zertifikatsvoraussetzungen vorliegen. **Kein** Router-Portforwarding wird automatisch eingerichtet.

## Nach der Installation mit Home Assistant verbinden

1. In **TAFA → Einstellungen** den Sprachmodus **Extern** auswählen.
2. In **TAFA → Verbindungen → CPU-Fallback** `http://CPU-SERVER-IP:5000` als Piper-Adresse eintragen.
3. In HA **Einstellungen → Geräte & Dienste → Wyoming Protocol** mit **CPU-SERVER-IP**, Port **10300**, verbinden.
4. Die tatsächliche Wyoming-`stt.*`-Entität unter **TAFA → Verbindungen → CPU-STT** auswählen. HA Core nach einer Backend-Aktualisierung einmal und TAFA nach Einstellungsänderungen gegebenenfalls neu starten.
5. In **Einstellungen → Sprachassistenten → TAFA Lokal** STT-Router, Gesprächsrouter und **Tablet Assist Stream** prüfen. Danach eine echte Sprachfrage testen.

## Bereits vorhandener zentraler HTTPS-/Nginx-Proxy

Wer 80/443 bereits über einen eigenen Proxy-CT nutzt, sollte **nicht** eine zweite Portweiterleitung erstellen. Im Ein-Zeilen-Installer **HTTPS mode: shared** auswählen, den **tatsächlichen CT-Identifier des bestehenden Proxys** eingeben und die geplante **neue, separate Audio-Site** ausdrücklich bestätigen. Es gibt **keine allgemeingültige Proxy-CT-ID**. Vorhandene Webseiten, Domains und Zertifikate vorher sichern und prüfen. Das Skript `proxmox/audit-shared-proxy.sh` liest die bestehende Nginx-Konfiguration nur aus.

Im Modus **shared** darf die Audio-Dateiausgabe gezielt für die IP des vorhandenen Proxys erreichbar sein, nicht für das ganze Internet. Im Modus **dedicated** bleibt der interne Audio-Dateiserver auf `127.0.0.1:8080`; ein zweiter Proxy-CT kann diesen Port nicht erreichen. Die Modi **dedicated**, **shared** und **none** sind getrennt zu wählen. Details: [Nginx-/HTTPS-Anleitung](nginx-proxy.md). Eine öffentliche Audio-Domain wird nur für **optionale Alexa-MP3-Nachrichten** gebraucht; `mp3_base` und `public_audio_base` müssen zum selben Backend gehören.

**DuckDNS:** Eine Subdomain zuerst im DuckDNS-Konto anlegen. Der optionale Updater benötigt den **DuckDNS-Kontotoken**; das ist **kein TAFA-API-Token** und gehört niemals ins Repository. Netzwerk-Firewall und öffentliche Freigaben getrennt prüfen.

## Abgebrochene Erstinstallation

Für einen **neu erstellten, noch leeren** CT oder die vom Wiederaufnahme-Skript ausdrücklich geprüfte unvollständige Python-venv:

```bash
curl -fsSLo /root/tafa-resume.sh https://raw.githubusercontent.com/michaelbudisch/tablet-assist-for-alexa/main/proxmox/resume-install.sh
bash /root/tafa-resume.sh
```

Der Assistent benötigt die **eigene** CT-ID und bei vorhandenem zentralen Proxy dessen **echte** CT-ID. Er ist **kein Reparaturskript für beliebige bestehende Produktionsinstallationen**. Falls Dienste bereits eingerichtet sind, zunächst Logs/Zustand prüfen und nicht erneut installieren.

## Prüfung im neuen CT

```bash
tafa-info
systemctl status jarvis-piper jarvis-mp3 jarvis-whisper jarvis-audio
curl -fsS http://127.0.0.1:5001/health
journalctl -u jarvis-whisper -n 50 --no-pager
```

Der Generator ist tokenfrei **nur im vertrauenswürdigen LAN** zu verwenden. Keine Freigaben für 5000, 5001, 10300 oder 8080 ins Internet. Die GPU-Variante wird unabhängig über [GPU Worker](worker.md) eingerichtet.

**Legacy:** Für die Aktualisierung eines **alten tokenbasierten MP3-Generators** existiert `proxmox/update-mp3-generator.sh`; das ist ein **Migrationsskript**, gehört nicht zur Erstinstallation und darf nicht auf dem PVE-Host ausgeführt werden.
