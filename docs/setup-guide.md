# TAFA – einfacher Einrichtungsassistent

[English](en/setup-guide.md) · [App installieren](app.md)

TAFA App **0.3.11** kann Piper/Whisper entweder lokal betreiben oder deinen vorhandenen **Proxmox-Sprachserver exklusiv nutzen**. Die Wahl erfolgt vor dem App-Start unter **Einstellungen → Apps → TAFA → Konfiguration**. Es gibt drei voneinander unabhängige Entscheidungen:

**Bestehender Proxmox-Sprachserver:** Um ausschließlich den bisherigen tokenpflichtigen MP3-Generator zu aktualisieren, die aktuellen Repository-Dateien im dedizierten Debian-Gast bereitstellen und dort `sudo bash proxmox/update-mp3-generator.sh` ausführen. Das Skript sichert die vorhandene `api.py`, startet nur `jarvis-mp3.service` neu und stellt bei Fehlern die Vorgängerversion wieder her. Piper, Whisper, Audiodateien und HTTPS-Proxy bleiben unverändert. Passend dazu TAFA-Integration 0.4.3 verwenden. **Nicht auf dem Proxmox-Host ausführen.** Port 5001 niemals ins Internet weiterleiten.

## 1. Wo sollen Piper und Whisper laufen?

| Variante | Ergebnis | Konfiguration |
|---|---|---|
| **TAFA lokal (Standard)** | Piper und Whisper laufen in der TAFA-App | App starten, HA einmal neu starten; die automatisierte TAFA-Lokal-Pipeline prüfen |
| **Externer Proxmox-Sprachserver** | Kein CPU-Modellstart in der TAFA-App | `speech_mode=external`, `external_piper_base=http://SERVER:5000`; App neu starten, danach Wyoming-STT `SERVER:10300` in HA hinzufügen |

Für Proxmox die [CPU-Sprachserver-Anleitung](proxmox.md) öffnen. Nur in einem **frischen Debian-Gast** `install-speechserver.sh` ausführen – **niemals auf dem Proxmox-Host** und niemals blind über eine vorhandene Jarvis-Installation. Ein neuer CT wird mit `create-ct.sh` auf dem Proxmox-Host nach ausdrücklicher Bestätigung erstellt (4 vCPU, 4 GiB RAM, 20 GiB Speicher, DHCP). Der Installer richtet außerdem optional nutzbare Dienste für MP3-Durchsagen ein.

Im externen Modus prüft das TAFA Control Center die Proxmox-Piper-API (`/health`) und versucht bei Erreichbarkeit, die TAFA-HA-Integration vorzubereiten. Unter **Einstellungen → Geräte & Dienste → TAFA → Optionen → Sprachserver & GPU** die externe Piper-Adresse kontrollieren, bei Wyoming die Integration für `SERVER:10300` hinzufügen und deren STT-Entität als **CPU-STT** auswählen. Anschließend unter **Einstellungen → Sprachassistenten** eine eigene Pipeline für TAFA mit STT-Router und **Tablet Assist Stream** erstellen. Die externe Proxmox-Piper-API besitzt selbst keinen `/stt`-Endpunkt, deshalb ist Wyoming zwingend für die externe Spracherkennung.

## 2. Soll der GPU-Hauptrechner die Qwen-Stimme übernehmen?

**Optional.** Mit Qwen wird die Sprachausgabe bevorzugt auf dem GPU-Rechner erzeugt; bei Ausfall **vor Beginn der Audioausgabe** übernimmt Piper.

Auf dem GPU-Rechner im Ordner `worker/`:

- Windows: `00-Konfiguration.bat` und `01-Installieren.bat` (oder das bestehende Worker-Update unverändert lassen)
- Linux: `bash setup-linux.sh`
- Danach `docker compose --profile stream up -d --build qwen-stream`

Die Skripte legen eine `.env` ausschließlich mit LAN-IP und Modelloptionen an. **Kein API-Token erforderlich.** Im TAFA-Menü **Sprachserver & GPU** folgende Angaben vornehmen:

| Feld | Angabe |
|---|---|
| Routing-Modus | **Automatisch** |
| GPU-Streaming-Adresse | `http://GPU-PC:10502` |
| GPU-Wyoming-STT | Optional, falls GPU-Whisper auf Port `10300` eingerichtet wurde |

**Wichtig:** Die Assist-Pipeline muss als Sprachausgabe **Tablet Assist Stream** auswählen, sonst bleibt die Qwen/Piper-Umschaltung trotz korrekter Zugangsdaten ungenutzt. Vorhandene Pipelines werden nicht automatisch geändert. Einzelheiten und optionale LLM-/Vision-Dienste: [GPU-Worker](worker.md).

## 3. Sollen Alexa-Echos MP3-Durchsagen erhalten?

**Nur dann** ist ein erreichbarer HTTPS-Audiohost nötig. Tablet → Echo per Bluetooth funktioniert unabhängig davon.

Der [Proxmox-Sprachserver](proxmox.md) enthält zusätzlich:

| Port | Aufgabe |
|---|---|
| `5001` | Tokenfreie MP3-Erzeugung nur im privaten LAN (`/generate`) |
| `8080` | Kurzlebige MP3-Dateien, nur für den internen Nginx-Proxy |

Für Alexa einen eigenen HTTPS-Hostnamen mit gültigem Zertifikat bereitstellen. Der [Nginx-Proxy-Leitfaden](nginx-proxy.md) beschreibt einen neuen CT oder das sichere Ergänzen eines bestehenden Proxy-CT. In **TAFA → Optionen → Alexa-Durchsagen & HTTPS** anschließend MP3-Generator und öffentliche HTTPS-Adresse und Raum-/Notify-Zuordnung angeben. Keine Ports 5000/5001/10300/10502 öffentlich freigeben. Die internen Generator-Ports niemals aus dem Internet erreichbar machen.

## Wo sind die Einstellungen?

1. **TAFA Control Center** unter Home Assistant **Apps → TAFA → Weboberfläche** öffnen. Dort sind Zustände und diese Schritte erklärt.
2. **Einstellungen → Geräte & Dienste → TAFA → Optionen** öffnen.
3. Einen Abschnitt auswählen: **Sprachserver & GPU**, **Alexa-Durchsagen & HTTPS** oder **Datenquellen & Erinnerungen**.
4. Werte speichern; TAFA lädt die Integration neu. GPU- und MP3-Generator benötigen keine zusätzlichen TAFA-API-Tokens. Ein leerer GPU-Host deaktiviert GPU-TTS.
5. **Einstellungen → Sprachassistenten → TAFA Lokal** prüfen. Für automatisches Qwen/Piper-TTS **Tablet Assist Stream** wählen.

## Kurzer Funktionstest

- **TAFA lokal:** Piper und Whisper im Control Center auf „Bereit“ prüfen; eine Assist-Anfrage manuell starten.
- **Externer Proxmox-Server:** `curl -fsS http://SERVER:5000/health` prüfen. In TAFA muss „Piper · extern“ bereit sein, lokal dürfen keine Piper-/Whisper-Downloads starten. Wyoming-STT `SERVER:10300` in HA einrichten, CPU-STT im TAFA-Optionsdialog auswählen und Assist-Pipeline erstellen.
- **GPU:** Qwen bei laufendem PC testen; PC ausschalten und dieselbe Assist-Ausgabe erneut prüfen → Piper-Fallback.
- **Alexa-MP3 (optional):** Eine unkritische Testdurchsage senden und die kurzlebige öffentliche HTTPS-Datei prüfen.

Die unveränderte **TAFA Device Bridge 1.0.0** meldet Rufwörter, überträgt aber nicht die folgende Frage. Ein aktiver Assist-Client mit Mikrofon ist dafür weiterhin notwendig. Das private TAFA-Dashboard wird nicht installiert.

Die Geräte-/Worker-Konfiguration ist nicht automatisch: Qwen-Host sowie DNS-/Router-/HTTPS-Einrichtung werden bewusst nicht durchs Netz ermittelt oder ungefragt verändert.
