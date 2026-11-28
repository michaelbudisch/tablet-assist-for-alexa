# Ambient-Profile und Ring-Vision-Diagnose (TAFA 0.4.99)

[English](en/ambient-ring-vision.md) · [Einrichtung](setup-guide.md) · [TAFA-Übersicht](../README.de.md)

## Ambient für mehrere Tablets

Das **TAFA Dashboard → Mehr → Einstellungen → TAFA Ambient** enthält eine zentrale Geräteauswahl. Jedes registrierte Tablet besitzt ein eigenes Ambient-Profil in Home Assistant. Die Einstellungen des einen Tablets überschreiben keine anderen Tablet-Profile. Die Daten bleiben in der jeweiligen HA-Installation und werden **nicht** in GitHub gespeichert.

Pro Tablet können Kalender, Annäherungssensor, Aktivierung, automatisches Öffnen, Schließregel, Anzeigezeit und Sensorkacheln eingestellt werden. Ein Sensor kann über seine vorhandene HA-Entitäts-ID zugeordnet werden. Die Anzeige verwendet dessen aktuellen Wert und Einheit. Bis zu zwölf Sensoren sind konfigurierbar; die Kugel zeigt auf kleinen Bildschirmen höchstens die ersten sechs Positionen.

Der Button **Dieses Display zuordnen** speichert eine lokale Display-Bindung **nur im Browser, auf dem der Button gedrückt wird**. Wird TAFA am PC verwendet, sollte damit nicht versehentlich die Bindung des Tablets ersetzt werden. Ohne eindeutige Gerätezuordnung wird keine fremde Tablet-Identität geraten. Änderungen werden nach dem Speichern mit einer Profilrevision synchronisiert; gleichzeitige Änderungen werden nicht still überschrieben.

## Ring-Kameras zuordnen

Im **TAFA Dashboard → Mehr → Einstellungen → Ring · Qwen-Kamerazuordnung** wählt man die beiden Ring-Entitäten **„Letzte Aufnahme“**, eine für die Haustür und eine für die Vorderseite. **Nicht die „Live-Ansicht“ auswählen.** TAFA prüft die Ring-Gerätezugehörigkeit beim Speichern. Die Zuordnung bleibt in den HA-Integrationsoptionen erhalten und ersetzt keine Automationen.

Für das lokale Vision-Modell wird der vorhandene GPU-Worker benötigt. Die Videoanalyse verwendet – bei verfügbarer Schnittstelle – zwölf zeitlich verteilte Bilder, eine strukturierte Auswertung und bei Bedarf eine Detailprüfung; die vorhandenen Fallback-Wege bleiben erhalten.

## Vision-Diagnose

Öffne **TAFA Dashboard → Zuhause → Kameras**. Unter **Ring · Vision-Diagnose** erscheinen die Kontaktbilder der zuletzt verarbeiteten Videoanalysen, die Zahl der Bilder, der Analysemodus und die KI-Szenenbeschreibung. Beim 4-Bilder-Fallback sind gegebenenfalls Einzelbild-Ergebnisse sichtbar.

Diese Vorschaubilder werden nur **bis zu 60 Minuten im Arbeitsspeicher** gehalten. Nach einem Home-Assistant-Neustart oder vor der ersten Analyse ist der Bereich leer. Die Diagnose-Seite startet **keine zusätzliche** Analyse, keinen Livestream und keine Alexa-Durchsage. Eine dauerhaft gespeicherte Analyse-Historie benötigt den Home-Assistant-Recorder beziehungsweise die bisherigen eigenen Protokollierungsautomationen.

## Ring-Bewegungs-Infobox

Für gekoppelte und berechtigte TAFA-Tablets bietet die Integration einen eingeschränkten Ereigniskanal. Er verarbeitet den TAFA-Ereignistyp `tafa_camera_notice` und für bestehende Installationen den bisherigen Typ `jarvis_infobox_show`. Ein Ereignis enthält mindestens eine konfigurierte Ring-Kamera (`camera`) sowie eine eindeutige Kennung (`request_id`); optional sind `title` und `seconds`. Der Kanal verarbeitet keine beliebigen Home-Assistant-Ereignisse.

Die Infobox zeigt **„Bewegung erkannt“** und, sofern vorhanden, das letzte Ring-Bild. Der Benachrichtigungsempfang startet keine Liveübertragung und erstellt keine KI-Beschreibung. Für eine automatische Ereignisauslösung müssen passende Ring-Automationen **separat vorhanden** sein. TAFA installiert oder verändert diese nicht ungefragt.

## Update und Datenschutz

Beim Aktualisieren von TAFA bleiben vorhandene Benutzerkonfigurationen, Profilrevisionen, Ring-Zuordnungen und Home-Assistant-Automationen erhalten. Geräte-IDs und Entitäts-IDs stammen ausschließlich aus der jeweiligen lokalen Installation. Der öffentliche Quellcode enthält keine Haushaltssensoren, API-Tokens oder privaten Automationen.

**Hinweis:** Der Stand dieses Dokuments beschreibt die Quellcode-Version 0.4.99. Ein Commit im GitHub-Hauptzweig ist **nicht** automatisch ein signierter Android-APK- oder Marketplace-/HACS-Release.
