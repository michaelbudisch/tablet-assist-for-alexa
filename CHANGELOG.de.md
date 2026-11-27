## TAFA-App / HA-Integration 0.4.49 — Ambient-Modul sauber getrennt
- Die eigenständige TAFA-Integration nutzt nun `tafa-ambient.integration.v1` statt des globalen Hauszentrale-Speichers. Dadurch kann sie den privaten Ambient-Modus nicht mehr überschreiben.
- Testdiagnostik ist nicht mehr Bestandteil der regulären Nachtansicht; private Testseite bleibt separat über ihre URL erreichbar.
- Die private Hauszentrale nutzt ab sofort `bag.parts.privateAmbient` und das eigene Ereignis `tafa-private-ambient-ready`.
- Versionsparameter der gelieferten Frontend-Module auf `?v=0.4.49` angehoben. Kugel, Sternschnuppen und bestehende Automationen bleiben erhalten.

## TAFA-App / HA-Integration 0.4.48 — Android-WebView Vollbildansicht und Diagnose
- Der Ambient-Nachtmodus ist auf Android als vom Lovelace-Kartenraster unabhängige Vollbild-Ansicht aufgebaut; dadurch werden problematische Tablet-Grid-Breiten nicht mehr vererbt.
- Eigener Tagesansicht-Button innerhalb des Vollbildes. Diagnosezeile zeigt laufende Frontend-Version, Browser-Viewport, tatsächliche Ansichtsbreite und Canvas-Status.
- Private Testseite `/local/tafa/ambient-webview-test-v0.4.48.html` zur Abgrenzung zwischen WebView- und Dashboard-Layout-Problemen. Hauptkarte und Ambient-Ressource verwenden `*-v0.4.48.js?v=0.4.48`.
- Kugelnetz und Sternschnuppen bleiben unverändert, ebenso Automationen und Sensorzuordnungen.

## TAFA-App / HA-Integration 0.4.47 — Natürliche Sternschnuppen im Ambient-Modus
- Ersetzt die dauerhaft gezeichneten Bogenlinien um die Kugel durch zufällig auftauchende 3D-Lichtimpulse mit leuchtendem Kopf und kurzem auslaufendem Schweif.
- Lichtimpulse besitzen unterschiedliche Bahnebene, Entfernung, Richtung, Geschwindigkeit, Helligkeit und Lebensdauer und verschwinden wieder. Das Kugelnetz, seine Linienbreite und der ruhige Standby-/KI-Puls-Modus bleiben unverändert.
- Die private TAFA-Hauptkarte und Ambient-Datei verwenden die neue Ressource `*-v0.4.47.js?v=0.4.47`; der Versionsmanifest wurde aktualisiert.
- Keine Automationen und Sensorzuordnungen verändert.

## TAFA-App / HA-Integration 0.4.46 — Frontend-Version prüfen und vollständige Aktualisierung
- Die Import-URLs für das ausgelieferte Dashboard und seine Begleitmodule sind auf `?v=0.4.46` erhöht.
- Das private Hauszentrale-Dashboard verwendet neue Dateien `/local/tafa/*-v0.4.46.js`; zusätzlich läuft ein optionaler Versionswächter. Er prüft die zur Laufzeit registrierte Dashboard-Klasse und bietet bei einem Versionskonflikt einen ausdrücklich bestätigten CacheStorage-Reset mit vollständigem Seitenwechsel an.
- Die private Hauszentrale-Karte und ihr Versionswächter werden nicht ins öffentliche Repository übernommen. Automationen und Einstellungen bleiben unverändert.

## TAFA-App / HA-Integration 0.4.45 — Versionsgebundene Frontend-Ressourcen
- Dashboard, Ambient-Modus und weitere JavaScript-Module erhalten neue `?v=0.4.45`-URLs; bei künftigen Frontend-Änderungen den Versionsparameter erhöhen.
- Im privaten HA-Dashboard werden die Hauptkarte und Ambient-Datei jetzt aus zwei separaten `/local/tafa/`-Dateien mit versioniertem Dateinamen und `?v=0.4.45` geladen. So erhalten selbst hartnäckige Android-WebViews beim Update eine neue URL.
- Die private Hauptkarte wird nicht in das öffentliche GitHub-Repository hochgeladen. Keine bestehenden Automationen oder Sensorzuordnungen geändert.

## TAFA-App / HA-Integration 0.4.44 — Ruhiger Ambient-Modus im Rufwort-Bereitschaftszustand
- Die vernetzte Kugel dreht sich im normalen Bereitschaftszustand ruhig und verformt/pulsiert nicht. Lichtpunkte und Orbitalbewegungen wurden entsprechend verlangsamt.
- Pulsieren, stärkere Verformung und lebhaftere Bewegung nur bei erkanntem Rufwort, aktiver Assist-Aufnahme, Verarbeitung oder Sprachausgabe.
- Status `listening: hey_jarvis` ist die dauerhafte Rufwortüberwachung und wird nicht länger irrtümlich als laufendes Gespräch behandelt.
- Die bereits eingebundene responsive Nachtansicht, 3D-Sensorwerte, bestehende Automationen und reguläre Tagesansicht bleiben unverändert.

## TAFA-App / HA-Integration 0.4.43 — 3D-Ambient und Tablet-Layout
- Die Kugel besteht jetzt aus einem unregelmäßigen 3D-Partikelnetz mit 96 Knoten, 220 unterschiedlich langen Verbindungen, Partikeln und kurzen orbitalen Bögen. Sensoranzeigen sind mit sechs 3D-Ankerpunkten verbunden, drehen sich perspektivisch mit und blenden abhängig von der Tiefe ab.
- Der Ambient-Modus setzt im Hoch- und Querformat die Navigationsspalte vollständig zurück und verwendet die verfügbare Breite. Die normale Dashboard-Navigation wird nicht verändert.
- Animationsdateien erhalten neue Versionsparameter für die Browser- und Tablet-WebView-Caches; vorhandene Automationen und Sensorzuordnungen bleiben unverändert.

## TAFA-App / HA-Integration 0.4.42 — Stabiler optionaler Ambient-Modus
- Der Ambient-Nachtmodus ist nun keine Voraussetzung mehr für das Starten des TAFA Dashboards. Wenn das Animationsmodul fehlt oder nicht geladen werden kann, bleiben Tagesdashboard und bestehende Nachtansicht verwendbar.
- Nachladen, Fehlerbehandlung, Abschalten beim Ansichtswechsel und laufende Sensoraktualisierung wurden abgesichert.
- Sprachantworten aus dem vorhandenen TAFA-/Jarvis-Ereignisweg können unten als animierte Infobox erscheinen. Keine Automationen verändert.

## TAFA-App / HA-Integration 0.4.41 — Ambient-Nachtmodus
- Zusätzlicher Animationsmodus im TAFA Dashboard: bewegte, vernetzte Lichtkugel, große Uhr, dynamische HA-Sensormesswerte und Spracherkennungs-Farbzustände.
- Header-Schalter für Ambient-Ansicht; Tagesdashboard, Sprachdienste und bestehende Automationen bleiben erhalten.
- TAFA-Assist-Ereignisse öffnen unten animierte Infoboxen für Antworten, Suchergebnisse und aktuelle Sensorwerte. Native Mikrofonstatus-Sensoren steuern die Farbzustände, soweit verfügbar.
- Separates, ressourcenschonendes Canvas-Modul mit sauberem Stoppen beim Ansichtswechsel; private Alt-Dashboard-Ansicht kann denselben Modus nutzen.

# Changelog

## TAFA-App 0.3.35 / HA-Integration 0.4.20 — Kamera-Kollision beim Übergang verhindern
- Während die bisherige Jarvis-Kamera noch installiert ist, registriert TAFA nur eigene Sprach- und Gesprächsentitäten. Kamera- und Bewegungssensoren werden erst aktiviert, wenn TAFA den Kameradienst selbst betreibt.
- Die neuen TAFA-Multiroom- und Mikrofon-Endpunkte bleiben aktiv. Keine Änderungen an bestehenden Automatisierungen, Kameras oder Pipelines.


## TAFA-App 0.3.34 / HA-Integration 0.4.19 / Android 1.0.2
- Ein einziger Sprachweg: Tablet-Mikrofon → Home Assistant („TAFA Lokal“) → Antwort auf dem gleichen Tablet per Bluetooth, inklusive Multiroom.
- Anschlussfragen pro Tablet in TAFA → Geräte einstellen: 0 bis 100 oder unbegrenzt (−1, bis zur Gesprächspause). Der alte feste App-Grenzwert entfällt.
- Der Mikrofon-Button in der Dashboard-Kopfzeile schaltet native Android-Rufworterkennung stumm/frei; bei mehreren Tablets mit expliziter Raumauswahl.
- TAFA erhält eigene authentifizierte REST-Endpunkte, übernimmt alte Gerätepaarungen lesend und verändert keine Automatisierungen.


## TAFA-App 0.3.33 / HA-Integration 0.4.18 — Sprachdienste im Dashboard-Design
- Der vorhandene TAFA-Menüpunkt öffnet die Sprachdienste wieder innerhalb des Dashboards, mit derselben Kopfzeile, Uhr und Navigation wie die übrigen Bereiche.
- Geräteverwaltung, Ansagen, Datenquellen, Lernfunktion und Sprach-Status nutzen dieselben dunklen Karten, Abstände und türkisfarbenen Akzente wie das ursprüngliche TAFA Dashboard. Die Ansicht wird beim Aktualisieren der HA-Sensoren nicht neu aufgebaut.
- Die unabhängig aufrufbaren Sprachdienste bleiben unter `/tablet_assist_for_alexa?view=voice` erreichbar. Keine bestehenden Automatisierungen oder Jarvis-Pipelines geändert.


## TAFA-App 0.3.32 / HA-Integration 0.4.17 — doppelte Kopfzeile entfernt
- Das ausgelieferte TAFA Dashboard zeigt keine zusätzliche Leiste mit „Dashboard / Sprachdienste / Dashboard einrichten“ mehr. Stattdessen steuern die vorhandene TAFA-Navigation unten und das Zahnrad in der Dashboard-Kopfzeile diese Funktionen.
- Der zurückführende Bedienbereich mit Speichern/Abbrechen erscheint nur während der Einrichtung oder beim Öffnen der Sprachdienste.
- Bestehende Jarvis-Pipelines, Automatisierungen und private Gerätezuordnungen bleiben unverändert.


## TAFA-App 0.3.31 / Integration 0.4.16 — keine Kollision mit TAFA-Home-Vorschau
- Das integrierte Dashboard und sein Editor erhalten eigene Web-Komponentennamen. So funktionieren bereits installierte Lovelace-Vorschau und neues TAFA-Panel gleichzeitig, ohne sich gegenseitig zu überschreiben.
- Keine Änderungen an Automatisierungen, privaten Lovelace-Einstellungen oder Jarvis-Pipelines.


## TAFA App 0.3.30 / Integration 0.4.15 — Dashboard ohne Piper installieren
- Die HA-Ersteinrichtung kann jetzt mit der ausdrücklich ausgewählten Option dashboard_only abgeschlossen werden, auch wenn Piper aktuell nicht erreichbar ist. Die normale Spracheinrichtung benötigt weiterhin einen bereiten Piper-Dienst.
- TAFA Dashboard kann sofort mit zentralen Gerätezuordnungen eingerichtet werden. Bestehende Automatisierungen bleiben unverändert.


## TAFA-App 0.3.29 / Integration 0.4.14 — das auslieferbare TAFA Dashboard
- Als Referenz diente eine lokale Kiosk-Version; haushaltsspezifische Sensor-IDs und private Jarvis-Dateien werden nicht veröffentlicht. Die portable, vom Original-Design abgeleitete TAFA-Home-Oberfläche ist direkt in die Integration eingebaut und öffnet sich jetzt standardmäßig statt der bisherigen TAFA Sprachzentrale.
- Die Sprachzentrale ist als Unterbereich **Sprachdienste** erreichbar, inklusive Geräteverwaltung, Ansagen und Lernfunktionen. Keine Automatisierungen werden verändert.
- Admins können Module aktivieren und Entitäten über die integrierte Oberfläche auswählen; die Konfiguration wird geräteübergreifend in Home Assistant gespeichert.


## TAFA-App 0.3.28 — Wyoming-Konflikt beim Speichern bereinigen
- Bereinigung der CPU-/GPU-Doppelzuordnung jetzt auch nach dem erneuten Lesen der neuesten Supervisor-Einstellungen unmittelbar vor dem Speichern eines bestätigten JSON-Imports.
- Importvorschau zeigt eine bereits bekannte Bereinigung. Unterschiedliche STT-Entitäten werden nicht verändert.


## TAFA-App 0.3.27 / HA-Integration 0.4.13 — CPU/GPU-Wyoming getrennt
- Wenn ein bestätigter GPU-/Proxmox-JSON-Import dieselbe STT-Entität in beiden Rollen vorfindet, wird nur die alte Gegenzuordnung gelöscht. Unterschiedliche CPU- und GPU-Anbieter bleiben unverändert.
- Der Import validiert die korrigierte Zielkonfiguration, nicht die bereits fehlerhafte alte. Auch die spätere Registrierung neuer Entitäten wird abgefangen.
- Die HA-Integration wählt eine ausdrücklich als GPU eingetragene Wyoming-STT-Entität nicht mehr automatisch als CPU.


## TAFA-App 0.3.25 / HA-Integration 0.4.12 — gelöschte Wyoming-Integration erneut einrichten
- Beim erneuten JSON-Import blockiert eine veraltete Zuordnung nach Löschen von Wyoming/Ollama in Home Assistant nicht mehr. Der passende Dienst wird neu angelegt, wenn verfügbar; fremde Integrationen bleiben unverändert.
- Statt nur »provision_failed« erscheinen die konkreten HA-Fehlergründe, beispielsweise »cannot_connect«. Die GPU-Worker-JSON muss nicht geändert werden.


## TAFA App 0.3.24 / Integration 0.4.11 — vollständigere Ersteinrichtung und gemeinsames Logo
- Frische App-Installationen starten im JSON-Einrichtungsmodus ohne Piper-/Whisper-Modelldownload. Nach Import verarbeitet TAFA verspätet registrierte Wyoming-/Ollama-Entitäten und führt die Erstellung der Assist-Pipeline „TAFA Lokal“ fort.
- Control Center und HA-Sprachzentrale nutzen den originalen zweifarbigen Android-App-Vektor. Eine Abschlusskarte zeigt den tatsächlichen Assist-Status und bietet den Link zur Standard-Auswahl, ohne bestehende Defaults zu überschreiben.


## TAFA-Integration 0.4.10 — Gerätezuordnung per bestätigtem JSON-Import
- Neue Admin-Schnittstelle für Wyoming-/Ollama-Einrichtung nach ausdrücklicher Freigabe im Control Center. Bestehende, nicht zugeordnete HA-Integrationen und Assist-Pipelines bleiben erhalten. Fehlende KI-Modelle werden nicht automatisch geladen.


## TAFA App 0.3.23 / GPU-Worker 2.2.4 — JSON-Import
- Worker und Proxmox-Sprach-CT erzeugen JSON mit stabiler Gerätekennung. Im TAFA Control Center kann die Datei geprüft und nach Bestätigung übernommen werden. Wyoming-/Ollama-Einrichtung erfolgt im HA-Backend; fremde Integrationen und Modelle bleiben unverändert. Bei IP-Wechsel wird dieselbe Gerätekennung erneut importiert.


## TAFA App 0.3.21 / GPU-Worker 2.2.3 — Endpunktstatus und kurze IP-Datei
- Für konfigurierte Piper-, Qwen-, GPU-Wyoming- und MP3-Adressen erscheint ein Live-Erreichbarkeitsstatus. TAFA zeigt den zuletzt gemeldeten STT-Rechner (GPU oder CPU) und schlägt die GPU-Whisper-IP aus der Qwen-IP vor, sofern beide auf demselben Rechner laufen.
- Die GPU-Worker-TXT enthält nur die bekannten GPU-Endpunkte mit den jeweiligen Eintragungsorten (DE/EN). Öffentliches HTTPS-Audio wird nicht automatisch aufgerufen.


## TAFA App 0.3.20 — Zentrale Einstellungsoberfläche
- Sprachserver, Wyoming CPU/GPU, Qwen, Ollama, Stimmen und Alexa werden an einer Stelle im TAFA Control Center verwaltet. Die native Home-Assistant-App-Konfiguration ist eine erweiterte Ansicht derselben gespeicherten Werte und kein zweiter Speicher.
- Einstellungen werden vor dem Speichern validiert; nach dem Speichern TAFA neu starten. Bei einer frischen Proxmox-Einrichtung kann `external` weiterhin vor dem allerersten Start über die native Konfiguration gewählt werden, damit keine lokalen Modelle geladen werden.


## TAFA App 0.3.19 — Docker-Startfehler behoben
- Die Datei `wyoming_picker.py` wird ins App-Image kopiert. In 0.3.18 verursachte ihr Fehlen einen `ModuleNotFoundError` beim Start.
- Importprüfung beim Build und Regressionstest ergänzt. Einstellungen, HA-Integration 0.4.9, GPU-Worker und Android-App unverändert.

## TAFA App 0.3.18 / GPU-Worker 2.2.2 — Ersteinrichtung vereinfachen
- GPU-Worker-Verbindungsdatei enthält jetzt eine vollständige deutsch-englische Anleitung für GPU-/CPU-Wyoming, Ollama sowie alle TAFA-Felder.
- Im **TAFA Control Center** werden vorhandene Wyoming-STT-Entitäten als getrennte **CPU-/GPU-Dropdowns** angeboten. Speichern übernimmt die Auswahl in die App-Optionen; TAFA-App danach neu starten.
- Deutlich erklärt, dass Qwen-TTS auf Port 10502 keine GPU-Whisper-Verbindung herstellt. Die neue Auswahl verändert keine anderen App-Optionen und deaktiviert keine bestehenden Modelle.



## TAFA App 0.3.17 / Integration 0.4.9 — Erste Ollama-Frage freigeben
- Home Assistant meldet bei neuen Gesprächsassistenten zunächst `unknown` („Unbekannt“), solange sie noch keine Frage erhalten haben. TAFA wertete dies fälschlich als Ausfall und blockierte die erste Frage.
- Jetzt wird `unknown` als gültiger Erstzustand behandelt. Nur tatsächlich fehlende, selbstreferenzierende oder `unavailable`-Agenten werden blockiert.
- Das CPU-/Homeserver-Profil beeinflusst weiterhin Piper/Qwen-TTS, deaktiviert aber nicht länger einen vorhandenen Ollama-Gesprächsassistenten. Android-APK unverändert.



## TAFA App 0.3.16 / Integration 0.4.8 — Native Spracheingabe vorbereiten
- Externer Proxmox-Sprachserver: Die App meldet erst dann `external_ready`, wenn eine vollständige Assist-Pipeline angelegt oder vorhanden ist; vorher wird die Einrichtung weiter geprüft.
- Unvollständige vorhandene Pipeline wird nicht überschrieben, sondern als `pipeline_needs_review` angezeigt.
- Unter **TAFA → Geräte → Sprachtest** sind die Voraussetzungen für native Android-Sprachaufnahmen (Device Bridge 1.0.1) in DE/EN beschrieben.



## TAFA App 0.3.15 / Integration 0.4.7 — Sprachausgabe-Test auch ohne HTTPS
- Unter **TAFA → Geräte → Sprachtest** gibt es einen **Sprachausgabe testen**-Knopf. Der Testtext wird per Qwen/Piper erzeugt und über den gekoppelten Tablet-/Bluetooth-Player abgespielt. Der Status berücksichtigt die Rückmeldung des Players.
- Funktioniert auch über HTTP im lokalen Netzwerk, ohne Browsermikrofon. Für **Einmal sprechen** mit Mikrofon bleibt HTTPS erforderlich; der nicht unterstützte Mikrofontest wird bei HTTP durch einen deutlichen Hinweis ersetzt.
- Keine Android-App-Änderung oder neuen Tokens.



## TAFA App 0.3.14 / Integration 0.4.6 — Sprachtest für frische Installationen
- Unter **TAFA → Geräte** lässt sich der bekannte **Einmal sprechen**-Test direkt durchführen: Browser-Mikrofon, Whisper, Assist, Qwen/Piper und Ausgabe auf dem verbundenen Tablet/Bluetooth-Lautsprecher.
- TAFA sucht selbst eine passende Assist-Pipeline; der Administrator kann gezielt ein gekoppeltes Tablet testen, andere Benutzer nur den eigenen Raum. Keine neuen Helfer oder Android-App-Änderungen.
- HTTPS für Browser-Mikrofon notwendig; Aufnahme endet beim Schließen des Tests.


## TAFA App 0.3.13 / Integration 0.4.5 — Tablet-Raumzuordnung
- Unter TAFA → Geräte kann ein Administrator jetzt direkt einen Audio-Raum und einen bestehenden HA-Benutzer ohne Adminrechte auswählen, speichern und den Verbindungsstatus prüfen.
- Kamerafreigabe pro Raum als separater Schalter (Standard: aus). Die Kamera wird nur am Tablet ausdrücklich gestartet; ein Administrator-Token ist für den Multiroom-Kamerastream nicht nötig. Beim Deaktivieren werden gespeicherte Bilder verworfen.
- Bestehende Audio-Sitzungen und Raum-Einstellungen bleiben bei unveränderter Zuordnung erhalten. Benutzerwechsel erfordern eine ausdrückliche Bestätigung.
- Keine Entwicklerwerkzeuge/YAML mehr für die Gerätezuordnung. Android-App 1.0.0 unverändert.



## TAFA App 0.3.12 / Integration 0.4.4 — zentrale Konfiguration
- Für App-Installationen werden Sprachserver, GPU, Alexa, Entitäten und Erinnerungen zentral unter Apps → TAFA → Konfiguration verwaltet.
- Die App überträgt Änderungen an bestehende App-eigene HA-Integrationen. Erweiterte Alt-Einstellungen bleiben bei der ersten Übernahme erhalten.
- Marketplace-Installationen behalten ihren bisherigen Konfigurationsweg. Vorhandene Assist-Pipelines werden nicht ersetzt.



## Unveröffentlicht — geführter Proxmox-Ein-CT-Installer
- Die Proxmox-Installer (Ein-CT sowie separate Sprachserver-/Proxy-CTs) lassen `pct create --password` das Root-Passwort bei der Erstellung verdeckt abfragen. Keine Passwortübergabe in der Kommandozeile; direkte Anmeldung an der CT-Konsole möglich.

- Geführte Proxmox-Installation, Wiederaufnahme und CT-Konsole vollständig auf Englisch; neuer Dialog für einen frei wählbaren, validierten CT-Hostnamen (Standard `tafa-voice`). Gilt für neue Installationsläufe, nicht rückwirkend für laufende CTs.
- Neues optionales Skript `proxmox/quick-install.sh`: lädt das Repository, führt durch CT-ID, Storage, Netzwerk, Ressourcen, GPU-Worker und Alexa-Hostname und erstellt nur nach Bestätigung einen neuen unprivilegierten Debian-CT.
- Piper, Wyoming-Whisper, MP3-Generator und Nginx laufen gemeinsam im neuen CT. MP3-Dateiausgabe auf 127.0.0.1:8080 begrenzt; die Generierungs-API (5001) bleibt ausschließlich fürs vertrauenswürdige LAN.
- `tafa-info`, `tafa-setup` und regelmäßig aktualisierter Konsolenbanner zeigen IPs, Ports und Dienste und ermöglichen eine bewusste spätere Zertifikatseinrichtung.
- Bestehende CTs, VMs, Routerregeln und Zertifikate werden nicht verändert. Sicherer PVE-Praxistest mit neuem CT noch ausstehend.


## TAFA-App 0.3.11 — Zentrale Einrichtung und Verbindungsstatus
- App-Konfiguration auf Deutsch/Englisch: Proxmox, GPU/Qwen, Fallback, Stimme, Klangprofil und Alexa-MP3.
- Control Center prüft Qwen, Piper-Reserve und MP3-Generator ohne Testdurchsage.
- TAFA-eigene Piper-/Whisper-Modelle nach Wechsel auf externe Sprache und Neustart gezielt löschbar; andere Installationen bleiben unberührt.
- Bei erster HA-Einrichtung werden die neuen App-Werte übernommen; bestehende HA-Einträge werden nicht ungefragt geändert.


## TAFA-App 0.3.10 / Integration 0.4.3 — externer Proxmox-Sprachserver
- Neuer optionaler Modus `speech_mode=external` in den App-Einstellungen: keine doppelten Piper-/Whisper-Prozesse oder Modell-Downloads in der HA-App.
- `local` bleibt Standard; Wyoming-STT und Assist-Pipeline im externen Modus bewusst in Home Assistant zuordnen.
- GPU Worker 2.2.1, Android Device Bridge 1.0.0, Nginx-Proxy und privates Dashboard unverändert.

## TAFA-Integration 0.4.3 / App 0.3.9 — lokale Dienste ohne zusätzliche Tokens
- TAFA-Optionen und lokale GPU-/MP3-Anfragen benötigen keinen zusätzlichen API-Schlüssel mehr.
- GPU Worker 2.2.1: Qwen, Vision, Diagnose und optional Ollama ohne TAFA-Tokens.
- Proxmox-MP3-Generator tokenfrei; öffentlicher HTTPS-Proxy liefert nur kurzlebige MP3-Dateien per GET.
- Home-Assistant-Anmeldung bleibt bestehen; Android Device Bridge und privates Dashboard unverändert.
- Worker-/Generator-Ports nur für vertrauenswürdige LAN-Geräte erlauben.


## TAFA-Integration 0.4.3 / App 0.3.9 — geführte Einrichtung
- Getrennte Optionsbereiche für lokale/Proxmox-Sprachserver, Qwen-GPU-Routing und Alexa-MP3/HTTPS.
- Control Center mit drei klaren Einrichtungsbereichen, Portübersicht und DE/EN-Anleitungen.
- Datenquellen und vorhandene Schlüssel bleiben erhalten, Android Device Bridge unverändert.
- Automatisierte Tests und HA-OS-Praxistest weiterhin erforderlich.


## Zusammengeführte TAFA-Integration 0.4.1 — Release-Kandidat
- Öffentliche TAFA-Oberfläche mit Geräteliste, Rufwortauswahl, Stummschaltung und Raumnamen.
- Erweiterte reale HA-Laufzeit-, Pipeline- und Ingress-Tests; App 0.3.4 mit Wiederanlauf des CPU-Sprachprozesses.
- Android Device Bridge 1.0.0 und privates Dashboard bleiben unverändert. Für stabilen Release fehlt der HA-OS-/Hardware-End-to-End-Test.


## TAFA-Integration 0.4.0 — Release-Kandidat
- Öffentliche HA-Backend-Module unter einer einzigen Integration zusammengeführt; native Rufwort-/Multiroom-Schnittstellen, Kamera, Vision und Sprachrouter eingeschlossen.
- TAFA Home-Assistant-App 0.3.2 enthält Piper und Faster-Whisper für CPU, automatische Einrichtung und ein zweisprachiges Control Center.
- Automatisierte Installations-, Quellcode- und Docker-Prüfungen. Neuinstallation unter echtem HA OS und Tablet-Bluetooth-Test stehen aus.
- Android Device Bridge 1.0.0 und privates Dashboard bleiben unverändert.


## TAFA Apps Vorschau 0.1.0
- Experimentelles HA-OS-App-Repository, Installer für mitgelieferte öffentliche Integrationen und Administrator-Ingress-Einrichtung ergänzt. Kein privates Dashboard und keine automatische Migration; Marketplace-Basisintegration bleibt 0.3.1.

## Unveröffentlicht — Marketplace-Backend-Konsolidierung
- Aktuelle Installationsgrenze und Ziel einer einzigen Integration dokumentiert; Android-Bezeichnung TAFA Device Bridge 1.0.0. Privates Dashboard bleibt ausgeschlossen. Kein neuer Integrationsrelease und keine Backend-Migration.

## Unveröffentlicht — Raum-Audio-Zuordnung im TAFA-Kiosk
- Wiederverwendbarer TAFA-Kompatibilitätsfix: Bei nachträglich vergebenen Adminrechten wird ein bereits zugewiesener Raumplayer weiterhin erkannt. Nicht zugewiesene Benutzer behalten den bisherigen Audio-Pfad.
- Eigene Multiroom-Raumkarte und Backend bleiben unverändert; getrennte Nicht-Admin-Benutzer für neue Räume bleiben Standard.
- DE/EN-Einbauanleitungen und Node-Regressionstests mit GitHub Actions; privater Kiosk-Quellcode wird nicht veröffentlicht.

## Unveröffentlicht — optionales lokales HTTPS / Split-DNS
- Optionaler Debian-/Proxmox-Installer für lokalen DNS auf einem bereits vorhandenen NGINX-/Certbot-Proxy. Keine Änderungen an HA, NGINX-vHosts, Zertifikaten oder Router.
- Deutsch/englische Anleitungen für Android-Mikrofon, Offlinebetrieb, Tests und Rückbau sowie Eingabe-/Syntaxtests.
- Keine neue Produkt- oder APK-Version; `VERSION` bleibt auf dem letzten veröffentlichten Stand.


## Raumbezogene Multiroom-Kameraerkennung — Backend 1.7.1
- Der administrative Vision-Check kann über `room` gezielt die freigegebene Raumkamera statt des alten globalen Kamerastreams verwenden.
- Raumbezogene Ereignisse `jarvis_echo_relay_detection` enthalten die Raumkennung; veraltete oder ersetzte Kamerasitzungen werden verworfen.
- DE/EN-Migrationsanleitung für die vorbereitete Büro-Begrüßung ohne doppelte Ansagen. Der bisherige Einzelgeräte-Modus bleibt erhalten.
- Die HA-Integration muss manuell aktualisiert und neu geladen werden; es erfolgt keine automatische Installation.


[English](CHANGELOG.md) | **Deutsch** · [Projektübersicht](README.de.md)

## Multiroom — Backend 1.7.0 / Android 0.6.0 / Raumkarten 0.2.0 und 0.1.1

- Getrenntes authentifiziertes Raum-Audio und optionale JPEG-Kamera-/Bewegungsentitäten; ausdrückliche Freigabe, RAM-Bilder, keine Identitätsverfolgung.
- Raumzuordnung, Ruhezeiten, gezielte Durchsagen, Bereichskontext und bessere Statusfehler; generischer Kiosk-Audioadapter, privates Dashboard ausgeschlossen.
- Veröffentlichte signierte Android-APK 0.6.0 unverändert. DE/EN-Anleitungen mit HTTPS und gleichem Raumkonto.
- Ein echtes Tablet und automatisierte Zwei-Raum-Tests bestanden; gleichzeitiger Hardwaretest und Neuinstallation offen.

## Native HA-Automationen — optionale Karte 1.3.0

- Erweitertes Vision-Schema mit grob geschätzten Erscheinungskategorien; unklare und ungültige Ergebnisse werden abgefangen.
- Optionale Familienhelfer, Sprachauftrag mit Bestätigung und native Begrüßungsautomation.
- Sprachausgabe und Begrüßung in bestehender Hauszentrale getestet; eigenständige Karte bleibt Vorschau.

## Echo Relay proaktiv — Backend 1.6.0 / Worker 1.9.0 / Karte 1.2.0

- Optionale Bewegungsauswertung mit festem Personen-/Hund-Ergebnis und grober Einschätzung erwachsen/Kind/unklar; keine Identitäts- oder Geschlechtserkennung.
- Wiederholbarer Testmodus zu jeder Uhrzeit mit Sperrzeit; Morgen-Zeitfenster und gespeicherte Tagesbegrenzung im Normalbetrieb.
- Regenhinweise aus HA-Vorhersagen, optionale feste Anrede, koordinierte native Audioausgabe und Ja/Nein-Rückfrage zum Tagesüberblick.
- Konfigurierte Kategorien/Skripte und Erkennungsereignis für native HA-Automationen. Offline, beschäftigt, veraltet oder unsicher löst keine Aktion aus.
- Gemeinsame DE/EN-Lovelace-Einstellungen, Bewegungsvorlage und isolierte Worker-/HA-/Browsertests. APK 0.5.0 bleibt unverändert.

## Lovelace-Einstellungen 1.1.0 / Bedienpanel 1.6.0

- Gemeinsame Oberfläche mit Theme-Farben und Reitern für Sprache/Audio, Anzeige/Kameras, KI/Leistung und Verlauf/Diagnose.
- Sichtbare Modell- und Helferauswahl statt Menüüberlagerungen; HA-Updates erhalten ausstehende Auswahlen, Speicherfehler stehen direkt am Feld.
- Eigenständige Karte mit gespeicherten Mikrofon-/Gesprächswerten, Untertiteln, Verlauf im Arbeitsspeicher und optionaler Tablet-Reserve.
- Lovelace-Vorlage und Installer enthalten die gemeinsamen Module; Hausfunktionen sind gruppiert. Kein APK-, Worker- oder Backend-Update nötig.

## 0.3.1 — Entwicklungsvorschau
- Kontextbezogene Folgefragen in derselben Unterhaltung, begrenzte Dauer und unterstützte lesende Themen.
- Optionale manuell freigegebene Lernfunktion für allgemeine nicht erkannte Hausdaten-Fragen; keine Audioaufnahmen, keine allgemeinen Transkriptlogs, begrenzte Vorschläge im RAM und lokale Alias-Speicherung.
- Eigene Administrationsseite Lernen, sicherer WebSocket-Zugriff, DE/EN-Texte und Tests.
- Übersetzungsschlüssel auf gültige ASCII-IDs umgestellt; alte gespeicherte Werte und Durchsage-API bleiben kompatibel.
- Home-Assistant-Konfigurationsschema ergänzt. HACS-Beschreibung/Topics müssen weiterhin im Repository gesetzt werden.

## 0.3.0 — Entwicklungsvorschau
- Flexible deutsche, lokale Absichtserkennung mit Wortnormalisierung, Synonymen und Zeitraumprüfung.
- Frei auswählbare Datenquellen in Integration → Optionen und Übersicht in der eigenen Sprachzentrale: Wetter, Bring!/To-do, Abfalltermine, Heizung, Geräte, Energie.
- Bring!-Einzelartikel hinzufügen, entfernen, prüfen und vorlesen; exakte Namensvergleiche und Prüfung nach Änderungen.
- Abfallabfragen bieten bestätigungspflichtige Erinnerungen an; ein persistenter Termin, HA-Benachrichtigung und optional Echo.
- Keine privaten Entitätszuordnungen, keine automatische Migration. Synthetische Tests und DE/EN-Dokumentation; echte HA-Installation ausstehend.

## 0.2.2 — Entwicklungsvorschau
- Vollständige DE/EN-Installations- und Projektdokumentation, lokalisierte Marketplace-Auswahlfelder und Karten.
- Eigenständige Sidebar-Sprachzentrale mit Assist-Start, Status, Bluetooth-Keepalive und Durchsagen; keine Abhängigkeit von Hauszentrale oder Legacy-Helfern.
- Deutsche Sprachverarbeitung und Legacy-Vorlagen unverändert; echte Neuinstallation weiterhin ausstehend.

## 0.2.1 — Entwicklungsvorschau
- Anleitung für DuckDNS-IP-Aktualisierung durch die Home Assistant App und getrennte Certbot-Zertifikate im Proxy-CT.
- Expliziter Shared-Proxy-Modus für einen neuen Audio-Hostnamen in einem vorhandenen Debian-Nginx-CT; keine Übernahme bereits vorhandener Sites.
- Prüfung auf Hostnamenkonflikte, Beibehaltung der Default-Site und bestehenden Certbot-Zeitplanung im Shared-Modus.
- Tests für die Hostnamenprüfung; bestehende Proxy- und HA-Installation bleibt unverändert.

## 0.2.0 — Entwicklungsvorschau
- Marketplace-kompatible Einzelintegration `tablet_assist_for_alexa` mit `hacs.json`, deutscher und englischer Einrichtung, STT- und TTS-Routing, Gesprächsmodus und optionaler Alexa-Ansageaktion.
- Verbindungsparameter und Klangprofile per Konfigurationsdialog statt Quellcode-Platzhaltern; optionale Assist-/Bluetooth-Karten enthalten.
- Separater unprivilegierter Nginx-Proxy-CT mit ACME/Certbot, begrenztem Audio-Pfad, Erneuerung und Installationsanleitung.
- Legacy-Installer und Timer-/Hinweisvorlagen bleiben erhalten. Keine automatische Migration; End-to-End-Test mit frischem Home Assistant und öffentlichem HTTPS ausstehend.

## 0.1.0 — Entwicklungsvorschau
- Initiale öffentliche Projektstruktur unter Tablet Assist for Alexa.
- CPU-Sprachserver mit Piper, Faster Whisper, MP3-Klangprofilen und Cache; Proxmox-/Debian-Installationsskripte.
- Bereinigte HA-Integrationen mit Gesprächsrouter, Live-Klangprofilen, Erinnerungen, konfigurierbaren automatischen Hinweisen und Dashboard-Karten.
- Original-GPU-Worker v1.5.0 mit Windows-Setup; zusätzlich Linux-Setup, ohne private Konfiguration.
- MIT-Lizenz für eigenen Code, getrennte Drittanbieter-Lizenzen.
- Quellprüfungen und lokale Audio-Tests. Neuinstallation, GPU-Inferenz und Gerätekompatibilität müssen praktisch geprüft werden.
