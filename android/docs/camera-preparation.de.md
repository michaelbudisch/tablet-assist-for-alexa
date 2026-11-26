# TAFA Tablet-Kamera einrichten

[English](camera-preparation.md) · [Aktuelle Device Bridge](../README.de.md) · [TAFA-Einrichtung](../../docs/setup-guide.md)

Diese Anleitung gilt für **TAFA Device Bridge 1.2.1** und die einheitliche **TAFA-Integration 0.4.26**. Die ältere separate Jarvis-Kamera-API ist für neue Installationen **nicht** erforderlich.

## Kamera für einen Raum aktivieren

1. Die TAFA-Integration und die [Android Device Bridge](../README.de.md) verbinden. Je Tablet einen **Nicht-Admin-HA-Raumnutzer** verwenden.
2. In Home Assistant **TAFA → Geräte & Multiroom → Tablet-Kameras je Raum** öffnen und die Kamera für den **richtigen Raum** ausdrücklich freigeben. Der Standard ist **Aus**.
3. Auf dem Tablet **TAFA Device Bridge → Einstellungen → Kamera** öffnen. Android-Kameraberechtigung erteilen, Front-/Rückkamera sowie Bildintervall (**1/2/3/5/10 Sekunden**) wählen. Bei Bedarf **Bildbewegung melden** aktivieren.
4. Auf dem Tablet **Kamera für HA starten** betätigen. **Allein durch die HA-Freigabe startet keine Aufnahme.** Ein Administrator-Token ist dafür nicht erforderlich.
5. Unter **HA → Geräte & Dienste → TAFA** die Kamera-/Bewegungsentitäten des Raums prüfen. Ohne frische Bilder oder ausgeschaltete Bewegungserkennung kann der Sensor als nicht verfügbar erscheinen.

TAFA überträgt **JPEG-Einzelbilder** über die authentifizierten TAFA-Raumkamera-Endpunkte. Ein Livevideo-Stream, dauerhafte Speicherung oder eine verlässliche Personen-/Paketerkennung ist damit **nicht** automatisch gegeben. Die optische Bewegungserkennung beruht auf groben Bildänderungen und kann sich irren. Die Kamerafunktion kann über die App oder die sichtbare Android-Benachrichtigung gestoppt werden.

## Optional: lokale Vision-Auswertung

Für Bildbeschreibungen wird ein separater kompatibler [GPU Worker mit Vision](../../worker/docs/README.de.md) und installiertem Bildmodell benötigt. Vision ist **nicht** Voraussetzung für das reine Kamera-Bild im Dashboard. Den Vision-Dienst nur im privaten LAN auf Port **10503** betreiben und die entsprechende Kamera-/Modellzuordnung in TAFA konfigurieren. Visionergebnisse sind unsicher und nicht zur Identifizierung von Personen geeignet.

**Datenschutz:** Kameras nur in Räumen verwenden, in denen alle Betroffenen informiert sind und die Aufnahme zulässig ist. Kamerafreigaben bei Nichtgebrauch deaktivieren. Keine internen Kamera-/Vision-Ports ins Internet weiterleiten.

Die [ältere Jarvis-Kameradokumentation](archive/legacy-camera-preparation.de.md) bleibt ausschließlich für Migrationen erhalten; sie ist **keine** Neuinstallationsanleitung.
