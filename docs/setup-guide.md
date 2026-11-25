# TAFA – einfacher Einrichtungsassistent

[English](en/setup-guide.md) · [App installieren](app.md)

> **Neu ab App 0.3.12:** Die TAFA-Einstellungen liegen zentral unter **Einstellungen → Apps → TAFA → Konfiguration**. Nach dem Speichern die App neu starten. Bei einem Update Home Assistant einmal neu starten, damit die Integration geladen wird, dann die App neu starten. Die HA-eigene Wyoming-Integration wird einmal unter Geräte & Dienste hinzugefügt; die TAFA-Auswahl und alle weiteren Einstellungen erfolgen in der App. Vorhandene Assist-Pipelines werden nicht überschrieben. Für reine Marketplace-Installationen bleibt der HA-Optionsdialog erhalten.


TAFA App **0.3.12** kann Piper/Whisper entweder lokal betreiben oder deinen vorhandenen **Proxmox-Sprachserver exklusiv nutzen**. Die Wahl erfolgt vor dem App-Start unter **Einstellungen → Apps → TAFA → Konfiguration**. Es gibt drei voneinander unabhängige Entscheidungen:

**Bestehender Proxmox-Sprachserver:** Um ausschließlich den bisherigen tokenpflichtigen MP3-Generator zu aktualisieren, die aktuellen Repository-Dateien im dedizierten Debian-Gast bereitstellen und dort `sudo bash proxmox/update-mp3-generator.sh` ausführen. Das Skript sichert die vorhandene `api.py`, startet nur `jarvis-mp3.service` neu und stellt bei Fehlern die Vorgängerversion wieder her. Piper, Whisper, Audiodateien und HTTPS-Proxy bleiben unverändert. Passend dazu TAFA-Integration 0.4.3 verwenden. **Nicht auf dem Proxmox-Host ausführen.** Port 5001 niemals ins Internet weiterleiten.

## 1. Wo sollen Piper und Whisper laufen?

| Variante | Ergebnis | Konfiguration |
|---|---|---|
| **TAFA lokal (Standard)** | Piper und Whisper laufen in der TAFA-App | App starten, HA einmal neu starten; die automatisierte TAFA-Lokal-Pipeline prüfen |
| **Externer Proxmox-Sprachserver** | Kein CPU-Modellstart in der TAFA-App | `speech_mode=external`, `external_piper_base=http://SERVER:5000`; App neu starten, danach Wyoming-STT `SERVER:10300` in HA hinzufügen |

Für Proxmox die [CPU-Sprachserver-Anleitung](proxmox.md) öffnen. Nur in einem **frischen Debian-Gast** `install-speechserver.sh` ausführen – **niemals auf dem Proxmox-Host** und niemals blind über eine vorhandene Jarvis-Installation. Ein neuer CT wird mit `create-ct.sh` auf dem Proxmox-Host nach ausdrücklicher Bestätigung erstellt (4 vCPU, 4 GiB RAM, 20 GiB Speicher, DHCP). Der Installer richtet außerdem optional nutzbare Dienste für MP3-Durchsagen ein.

Im externen Modus prüft das TAFA Control Center die Proxmox-Piper-API (`/health`) und versucht bei Erreichbarkeit, die TAFA-HA-Integration vorzubereiten. Unter **Apps → TAFA → Konfiguration** die externe Piper-Adresse kontrollieren, die Wyoming-Integration für `SERVER:10300` einmalig hinzufügen; die STT-Entität im Feld `cpu_stt` der TAFA-App eintragen (oder automatisch erkennen lassen). Anschließend unter **Einstellungen → Sprachassistenten** eine eigene Pipeline für TAFA mit STT-Router und **Tablet Assist Stream** erstellen. Die externe Proxmox-Piper-API besitzt selbst keinen `/stt`-Endpunkt, deshalb ist Wyoming zwingend für die externe Spracherkennung.

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

Für Alexa einen eigenen HTTPS-Hostnamen mit gültigem Zertifikat bereitstellen. Der [Nginx-Proxy-Leitfaden](nginx-proxy.md) beschreibt einen neuen CT oder das sichere Ergänzen eines bestehenden Proxy-CT. In **Apps → TAFA → Konfiguration** anschließend MP3-Generator und öffentliche HTTPS-Adresse und Raum-/Notify-Zuordnung angeben. Keine Ports 5000/5001/10300/10502 öffentlich freigeben. Die internen Generator-Ports niemals aus dem Internet erreichbar machen.

### Alexa Devices: für Qwen-MP3 »Sprechen« statt »Durchsagen« verwenden

**Im getesteten Setup mit der Home-Assistant-Integration „Alexa Devices“:** Die Entität **„Durchsagen“** (`notify.…_durchsagen`) spielte nur den Alexa-Ankündigungston, jedoch nicht die generierte MP3-Datei. Mit **„Sprechen“** (`notify.…_sprechen`) wurde die Qwen-MP3 tatsächlich abgespielt. TAFA übergibt einen `<audio src="https://…/datei.mp3"/>`-Tag an die Notify-Entität. Normale Text-Durchsagen können auf „Durchsagen“ trotzdem funktionieren; das beweist noch keine MP3-Unterstützung.

1. Unter **Einstellungen → Geräte & Dienste → Entitäten** die exakte Entity-ID von **„[Echo-Name] – Sprechen“** kontrollieren (nicht den Anzeigenamen übernehmen).
2. In **Einstellungen → Apps → TAFA → Konfiguration → Alexa-Räume (JSON)** die Sprechen-Entität eintragen, z. B.:

   ```json
   {"Büro":{"notify":"notify.buro_dot_sprechen"}}
   ```

3. App-Konfiguration speichern, TAFA neu starten und die Testdurchsage unter **TAFA → Alexa-Durchsage** erneut auslösen. Bei Bedarf die HA-Integration neu laden.

Bei **Gong ohne Sprache** zuerst die verwendete Notify-Entität prüfen und danach testen, ob die erzeugte MP3-Datei über die öffentliche HTTPS-Adresse abrufbar ist. **„Sprechen“** erzeugt nicht zwingend den Alexa-Ankündigungsgong; falls gewünscht, den **TAFA-Signalton** für MP3-Durchsagen aktivieren. Die Zuordnung gilt für das getestete Alexa-Devices-Setup; andere Alexa-Integrationen können andere Möglichkeiten haben.

### Tablet und Multiroom ohne YAML einrichten

1. Android **TAFA Device Bridge → Verbinden** mit einem aktiven, **nicht-administrativen HA-Benutzer** und dessen persönlichem Token verbinden; unter **Rufwort** die Erkennung starten, damit das Gerät unter **TAFA → Geräte** registriert wird.
2. Als **HA-Administrator** unter **TAFA → Geräte** das erkannte Tablet öffnen. Dort **Multiroom-Audio → HA-Benutzer** auswählen; die vorgeschlagene Raumkennung bestätigen und **Audio-Raum verbinden** klicken. Bereits verbundene Räume und Player werden bei unveränderter Zuordnung nicht getrennt.
3. Falls das Tablet zuvor einem anderen HA-Benutzer zugeordnet war, muss der Administrator die Übertragung ausdrücklich bestätigen; anschließend auf dem Tablet den neuen Benutzer-Token verwenden.
4. Auf dem Tablet **Multiroom-Audio** aktivieren und **Player starten**. Der Status unter **TAFA → Geräte** zeigt „Audio verbunden“, „Player offline“ oder „Wiedergabe noch nicht bereit“ an. Für letzteres den Bluetooth-Medienausgang prüfen.
4. **Kamerazugriff (optional):** Unter **TAFA → Geräte → Multiroom-Audio** den Schalter **„Kamerazugriff für diesen Raum erlauben“** bewusst aktivieren. Standardmäßig ist die Kamera für jeden Raum deaktiviert. Anschließend auf dem Tablet **Multiroom-Audio** eingeschaltet lassen und die Kameraübertragung *ausdrücklich* starten. Der Raum-Benutzer-Token genügt, ein Administrator-Token ist nicht erforderlich. Die Freigabe startet niemals automatisch die Kamera; Deaktivieren verwirft gepufferte Bilder.

**Wichtig:** Die Rufwort-Geräteliste und die Audio-Räume sind getrennte Dienste. „Tablet registriert“ beweist nicht, dass der Audio-Player verbunden ist. Der Audio-Raum benötigt einen **eigenen aktiven HA-Benutzer ohne Administratorrechte**; der Administrator ordnet diesen über das TAFA-Dashboard zu, statt über Entwicklerwerkzeuge. Ein Token wird nie im Dashboard angezeigt oder hinterlegt. Der alte Helfer `input_text.jarvis_native_audio_command` ist im Multiroom-Modus nicht erforderlich.



### Sprachausgabe über die lokale HTTP-Adresse testen

Ist die Tablet-Audioverbindung unter **TAFA → Geräte** grün, lässt sich dort unter **Sprachtest** die neue Schaltfläche **„Sprachausgabe testen“** verwenden. Du kannst den Testtext ändern und mit einem Klick Qwen/Piper über die gewählte **TAFA Lokal**-Assist-Pipeline sprechen lassen. Die Testansage wird ausschließlich an den zugeordneten Android-/Bluetooth-Player gesendet. TAFA zeigt **Erzeugung → Übertragung → Wiedergabe → bestätigt/fehlgeschlagen** an. Diese Funktion benötigt **kein Browser-Mikrofon** und funktioniert auch bei lokaler HTTP-Nutzung.

**„Einmal sprechen“** bleibt der vollständige Mikrofon- und Assist-Test; hierfür verlangt der Browser eine vertrauenswürdige HTTPS-Adresse (oder localhost). Auf einer reinen HTTP-Adresse wird der Mikrofontest daher nicht eingeblendet und es erscheint eine Erklärung statt eines irreführenden Fehlers. Die HTTP-Audio-Testfunktion erfordert einen verbundenen, bereiten Tablet-Player und einen gültigen HA-Benutzer, keine neuen Tokens oder Android-App-Updates.

### Sprachtest nach der Tablet-Einrichtung

**TAFA → Geräte → [Tablet] → Sprachtest · Einmal sprechen** aufrufen und den Abschnitt aufklappen. TAFA wählt die vorhandene **TAFA Lokal**-Assist-Pipeline mit Whisper und **Tablet Assist Stream** automatisch; andere vollständige Pipelines lassen sich auswählen. Tippe auf **Einmal sprechen**, erlaube dem Browser das Mikrofon, stelle eine kurze Frage und höre die Antwort über den verbundenen Tablet-/Bluetooth-Player. Das verwendet den bereits getesteten Assist- und Multiroom-Audioweg, keine zusätzlichen HA-Helfer oder Scripts.

Der Browser benötigt eine **vertrauenswürdige HTTPS-Adresse** (oder localhost) für Mikrofonzugriff. Der Test kann auch mit einem angemeldeten HA-Administrator gezielt auf einen ihm angezeigten, bereits gekoppelten Tablet-Raum ausgeben; reguläre Tablet-Benutzer testen ausschließlich ihren eigenen Audio-Raum. Die Sprachausgabe wählt wie gewohnt Qwen mit Piper als Fallback. Beim Verlassen der Seite beziehungsweise Schließen des Sprachtests wird die Mikrofonaufnahme gestoppt. Wenn keine vollständige Assist-Pipeline (STT + TTS) existiert, wird auf die HA-Sprachassistenten-Konfiguration verwiesen.

Der Sprachtest ist eine Funktion des **HA-Browsers/Dashboards**. Die Android **Device Bridge 1.0.0** überträgt weiterhin nur das Rufwort-Ereignis, nicht die nachfolgende Frage aus dem Hintergrund.

### Neue Android-Sprachaufnahme (Device Bridge 1.0.1)

Für **Hey Jarvis → Frage → Whisper → Qwen/Piper → Bluetooth** braucht Android die Home-Assistant-Assist-Pipeline **TAFA Lokal** mit drei Komponenten: TAFA-Sprachrouter (Whisper/STT), TAFA-Gesprächsrouter und TAFA-Stream (TTS). Die TAFA-App erstellt diese Pipeline automatisch, sobald alle drei HA-Entitäten vorhanden sind – auch bei **externem Proxmox-Sprachserver**. Vorher zeigt die App **waiting_for_entities** statt fälschlich **external_ready**. Voraussetzung im externen Modus: Wyoming-STT von deinem Sprachserver in Home Assistant einrichten. Ist genau eine Wyoming-STT-Entität vorhanden, wählt TAFA sie automatisch; bei mehreren die gewünschte Entität in **Einstellungen → Apps → TAFA → Konfiguration → cpu_stt** auswählen.

Unter **TAFA → Geräte → Sprachtest** wird angezeigt, ob eine vollständige Assist-Pipeline konfiguriert ist. Das prüft die Konfiguration, **nicht** die Live-Erreichbarkeit von Whisper. Auf Android 1.0.1 dann unter **Rufwort → Native Sprachunterhaltung** den optionalen Modus einschalten; die bestehende Gerätezuordnung und der normale HA-Benutzer-Token bleiben erhalten. Für die native Aufnahme ist kein Browsermikrofon und kein Browser-HTTPS nötig. Lokales HTTP bleibt auf dem Transportweg unverschlüsselt. Die Android-App 1.0.1 muss weiterhin mit dem Original-Signierschlüssel erstellt werden.

## Wo sind die Einstellungen?

**Erster Schritt:** Unter **Einstellungen → Apps → TAFA → Konfiguration** die Adressen für Proxmox/Piper, GPU/Qwen und Alexa-MP3 sowie den automatischen Piper-Fallback, Stimmen und Klangprofile festlegen. Danach App neu starten. Die **Verbindungsdiagnose** und das gezielte Löschen TAFA-eigener CPU-Modelle befinden sich unter **Apps → TAFA → Weboberfläche**. Bestehende App-eigene HA-Einträge werden beim Neustart automatisch synchronisiert.


1. **TAFA Control Center** unter Home Assistant **Apps → TAFA → Weboberfläche** öffnen. Dort sind Zustände und diese Schritte erklärt.
2. **Einstellungen → Apps → TAFA → Konfiguration** öffnen.
3. Einen Abschnitt auswählen: **Sprachserver & GPU**, **Alexa-Durchsagen & HTTPS** oder **Datenquellen & Erinnerungen**.
4. Werte speichern; TAFA lädt die Integration neu. GPU- und MP3-Generator benötigen keine zusätzlichen TAFA-API-Tokens. Ein leerer GPU-Host deaktiviert GPU-TTS.
5. **Einstellungen → Sprachassistenten → TAFA Lokal** prüfen. Für automatisches Qwen/Piper-TTS **Tablet Assist Stream** wählen.

## Kurzer Funktionstest

- **TAFA lokal:** Piper und Whisper im Control Center auf „Bereit“ prüfen; eine Assist-Anfrage manuell starten.
- **Externer Proxmox-Server:** `curl -fsS http://SERVER:5000/health` prüfen. In TAFA muss „Piper · extern“ bereit sein, lokal dürfen keine Piper-/Whisper-Downloads starten. Wyoming-STT `SERVER:10300` in HA einrichten, CPU-STT über das Feld `cpu_stt` in der App einstellen (bei eindeutigem Wyoming automatisch) und Assist-Pipeline erstellen.
- **GPU:** Qwen bei laufendem PC testen; PC ausschalten und dieselbe Assist-Ausgabe erneut prüfen → Piper-Fallback.
- **Alexa-MP3 (optional):** Eine unkritische Testdurchsage senden und die kurzlebige öffentliche HTTPS-Datei prüfen.

Die unveränderte **TAFA Device Bridge 1.0.0** meldet Rufwörter, überträgt aber nicht die folgende Frage. Ein aktiver Assist-Client mit Mikrofon ist dafür weiterhin notwendig. Das private TAFA-Dashboard wird nicht installiert.

Die Geräte-/Worker-Konfiguration ist nicht automatisch: Qwen-Host sowie DNS-/Router-/HTTPS-Einrichtung werden bewusst nicht durchs Netz ermittelt oder ungefragt verändert.

### Ollama antwortet bei der ersten Frage nicht (TAFA 0.3.17 / Integration 0.4.9)

Ein neuer Ollama-Gesprächsassistent hat in Home Assistant bis zum ersten Aufruf den Zustand `unknown` („Unbekannt“). Dies ist **normal**; TAFA hat dies bis Integration 0.4.8 fälschlich blockiert. Seit 0.4.9 wird die Frage weitergereicht. Die echte Entitäts-ID des Ollama-Agenten unter **Einstellungen → Geräte & Dienste → Ollama → Gesprächsassistent → Entität** ablesen und unter **Apps → TAFA → Konfiguration → llm_agent** speichern. Nach dem TAFA-App-Update **Home Assistant Core einmal neu starten**, anschließend **TAFA-App neu starten**, um die Einstellungen zu synchronisieren. `unavailable` ist weiterhin ein tatsächlicher Fehlerzustand. Das CPU-Hardwareprofil regelt nur Qwen/Piper-Sprachausgabe und unterbindet Ollama nicht länger. Die Android-App muss dafür nicht geändert werden.
