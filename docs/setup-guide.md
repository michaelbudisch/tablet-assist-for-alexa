# TAFA – einfacher Einrichtungsassistent

[English](en/setup-guide.md) · [App installieren](app.md)

Die TAFA-Home-Assistant-App enthält ein **lokales CPU-Standardsystem** mit Piper und Faster-Whisper. Für eine normale erste Einrichtung musst du **keinen** Proxmox-Sprachserver, GPU-Rechner oder HTTPS-Proxy installieren. Es gibt drei voneinander unabhängige Entscheidungen:

## 1. Wo sollen Piper und Whisper laufen?

| Variante | Ergebnis | Konfiguration |
|---|---|---|
| **TAFA lokal (Standard)** | Piper und Whisper laufen in der TAFA-App | App starten, HA einmal neu starten; die automatisierte TAFA-Lokal-Pipeline prüfen |
| **Externer Proxmox-Sprachserver** | Piper/Whisper laufen in einem separaten Debian-CT/VM | Piper `http://SERVER:5000`, Wyoming-STT `SERVER:10300` |

Für Proxmox die [CPU-Sprachserver-Anleitung](proxmox.md) öffnen. Nur in einem **frischen Debian-Gast** `install-speechserver.sh` ausführen – **niemals auf dem Proxmox-Host** und niemals blind über eine vorhandene Jarvis-Installation. Ein neuer CT wird mit `create-ct.sh` auf dem Proxmox-Host nach ausdrücklicher Bestätigung erstellt (4 vCPU, 4 GiB RAM, 20 GiB Speicher, DHCP). Der Installer richtet außerdem optional nutzbare Dienste für MP3-Durchsagen ein.

Nach der Installation unter **Einstellungen → Geräte & Dienste → TAFA → Optionen → Sprachserver & GPU** die externe Piper-Adresse eingeben. Bei Wyoming unter Home Assistant die Integration für `SERVER:10300` hinzufügen und anschließend die entsprechende STT-Entität wählen. Die App-eigene CPU-Sprachverarbeitung wird dadurch **aktuell nicht automatisch abgeschaltet**; diese Wahl ändert das HA-Routing, nicht die Container-Laufzeit.

## 2. Soll der GPU-Hauptrechner die Qwen-Stimme übernehmen?

**Optional.** Mit Qwen wird die Sprachausgabe bevorzugt auf dem GPU-Rechner erzeugt; bei Ausfall **vor Beginn der Audioausgabe** übernimmt Piper.

Auf dem GPU-Rechner im Ordner `worker/`:

- Windows: `./Setup.ps1` in PowerShell (bei Windows üblicherweise `.\Setup.ps1`)
- Linux: `bash setup-linux.sh`
- Danach `docker compose --profile stream up -d --build qwen-stream`

Die Skripte legen die `.env` mit dem geheimen `JARVIS_TTS_TOKEN` an, sofern noch keine existiert. Im TAFA-Menü **Sprachserver & GPU** folgende Angaben vornehmen:

| Feld | Angabe |
|---|---|
| Routing-Modus | **Automatisch** |
| GPU-Streaming-Adresse | `http://GPU-PC:10502` |
| Qwen-API-Schlüssel | Wert von `JARVIS_TTS_TOKEN` aus der lokalen `.env` |
| GPU-Wyoming-STT | Optional, falls GPU-Whisper auf Port `10300` eingerichtet wurde |

**Wichtig:** Die Assist-Pipeline muss als Sprachausgabe **Tablet Assist Stream** auswählen, sonst bleibt die Qwen/Piper-Umschaltung trotz korrekter Zugangsdaten ungenutzt. Vorhandene Pipelines werden nicht automatisch geändert. Einzelheiten und optionale LLM-/Vision-Dienste: [GPU-Worker](worker.md).

## 3. Sollen Alexa-Echos MP3-Durchsagen erhalten?

**Nur dann** ist ein erreichbarer HTTPS-Audiohost nötig. Tablet → Echo per Bluetooth funktioniert unabhängig davon.

Der [Proxmox-Sprachserver](proxmox.md) enthält zusätzlich:

| Port | Aufgabe |
|---|---|
| `5001` | Authentifizierte MP3-Erzeugung (`/generate`) |
| `8080` | Kurzlebige MP3-Dateien, nur für den internen Nginx-Proxy |

Für Alexa einen eigenen HTTPS-Hostnamen mit gültigem Zertifikat bereitstellen. Der [Nginx-Proxy-Leitfaden](nginx-proxy.md) beschreibt einen neuen CT oder das sichere Ergänzen eines bestehenden Proxy-CT. In **TAFA → Optionen → Alexa-Durchsagen & HTTPS** anschließend MP3-Generator, `PIPER_API_TOKEN` aus `/etc/jarvis-local.env`, öffentliche HTTPS-Adresse und Raum-/Notify-Zuordnung angeben. Keine Ports 5000/5001/10300/10502 öffentlich freigeben. Niemals Tokens in Chat, Screenshots oder GitHub veröffentlichen.

## Wo sind die Einstellungen?

1. **TAFA Control Center** unter Home Assistant **Apps → TAFA → Weboberfläche** öffnen. Dort sind Zustände und diese Schritte erklärt.
2. **Einstellungen → Geräte & Dienste → TAFA → Optionen** öffnen.
3. Einen Abschnitt auswählen: **Sprachserver & GPU**, **Alexa-Durchsagen & HTTPS** oder **Datenquellen & Erinnerungen**.
4. Werte speichern; TAFA lädt die Integration neu. Passwortfelder leer lassen, um gespeicherte Schlüssel beizubehalten. Ein leerer GPU-Host deaktiviert GPU-TTS.
5. **Einstellungen → Sprachassistenten → TAFA Lokal** prüfen. Für automatisches Qwen/Piper-TTS **Tablet Assist Stream** wählen.

## Kurzer Funktionstest

- **TAFA lokal:** Piper und Whisper im Control Center auf „Bereit“ prüfen; eine Assist-Anfrage manuell starten.
- **Externer Proxmox-Server:** `curl -fsS http://SERVER:5000/health` von einem erreichbaren Gerät; Wyoming-STT-Entität in HA verfügbar prüfen.
- **GPU:** Qwen bei laufendem PC testen; PC ausschalten und dieselbe Assist-Ausgabe erneut prüfen → Piper-Fallback.
- **Alexa-MP3 (optional):** Eine unkritische Testdurchsage senden und die kurzlebige öffentliche HTTPS-Datei prüfen.

Die unveränderte **TAFA Device Bridge 1.0.0** meldet Rufwörter, überträgt aber nicht die folgende Frage. Ein aktiver Assist-Client mit Mikrofon ist dafür weiterhin notwendig. Das private TAFA-Dashboard wird nicht installiert.

Die Geräte-/Worker-Konfiguration ist nicht automatisch: Qwen-Host und Token sowie DNS-/Router-/HTTPS-Einrichtung werden bewusst nicht durchs Netz ermittelt oder ungefragt verändert.
