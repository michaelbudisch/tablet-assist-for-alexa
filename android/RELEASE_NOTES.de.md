# HA Jarvis Echo Relay 0.7.1 · experimentell

Dieser Testzweig ergänzt eine wahlweise lokale Vosk-Rufworterkennung mit vier Modi: Hey Jarvis, Jarvis, Alexa oder alle drei. Die Mikrofonberechtigung wird erst beim Start angefordert, das etwa 45 MB große Offline-Modell wird nur auf Knopfdruck installiert und lediglich erkannte Rufwörter werden an Home Assistant gemeldet (kein Audio). Ein Dashboard-Empfänger öffnet die bisherige STT-Pipeline. Über die sichtbare Benachrichtigung kann man den Dienst stoppen.

**Testzweig, noch keine veröffentlichte signierte APK.** Modellstart, Erkennungsqualität, Hintergrundbetrieb, Audioübergabe und Kompatibilität müssen auf dem echten Android-Tablet geprüft werden. Die veröffentlichte signierte Version 0.6.0 bleibt vorerst die stabile Downloadversion.

In 0.7.1 zusätzlich: Native Mikrofon-Stummschaltung und einstellbare Rufwörter, Bestätigungsanzahl, Sperrzeit und Übergabepause über App und Home Assistant. Die Stummschaltung gibt das Mikrofon frei; bei HA-Verbindungsverlust bleibt es aus. Der dB-Schwellwert ist weiterhin nicht verfügbar.
