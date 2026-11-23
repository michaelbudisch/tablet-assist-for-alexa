[English](CHANGELOG.md) | **Deutsch**

# Changelog

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

## 0.2.1 — Developer Preview
- Anleitung für DuckDNS-IP-Aktualisierung durch die Home Assistant App und getrennte Certbot-Zertifikate im Proxy-CT.
- Expliziter Shared-Proxy-Modus für einen neuen Audio-Hostnamen in einem vorhandenen Debian-Nginx-CT; keine Übernahme bereits vorhandener Sites.
- Prüfung auf Hostnamenkonflikte, Beibehaltung der Default-Site und bestehenden Certbot-Zeitplanung im Shared-Modus.
- Tests für die Hostnamenprüfung; bestehende Proxy- und HA-Installation bleibt unverändert.

## 0.2.0 — Developer Preview
- Marketplace-kompatible Einzelintegration `tablet_assist_for_alexa` mit `hacs.json`, deutscher und englischer Einrichtung, STT- und TTS-Routing, Gesprächsmodus und optionaler Alexa-Ansageaktion.
- Verbindungsparameter und Klangprofile per Konfigurationsdialog statt Quellcode-Platzhaltern; optionale Assist-/Bluetooth-Karten enthalten.
- Separater unprivilegierter Nginx-Proxy-CT mit ACME/Certbot, begrenztem Audio-Pfad, Erneuerung und Installationsanleitung.
- Legacy-Installer und Timer-/Hinweisvorlagen bleiben erhalten. Keine automatische Migration; End-to-End-Test mit frischem Home Assistant und öffentlichem HTTPS ausstehend.

## 0.1.0 — Developer Preview
- Initiale öffentliche Projektstruktur unter Tablet Assist for Alexa.
- CPU-Sprachserver mit Piper, Faster Whisper, MP3-Klangprofilen und Cache; Proxmox-/Debian-Installationsskripte.
- Bereinigte HA-Integrationen mit Gesprächsrouter, Live-Klangprofilen, Erinnerungen, konfigurierbaren automatischen Hinweisen und Dashboard-Karten.
- Original-GPU-Worker v1.5.0 mit Windows-Setup; zusätzlich Linux-Setup, ohne private Konfiguration.
- MIT-Lizenz für eigenen Code, getrennte Drittanbieter-Lizenzen.
- Quellprüfungen und lokale Audio-Tests. Neuinstallation, GPU-Inferenz und Gerätekompatibilität müssen praktisch geprüft werden.
