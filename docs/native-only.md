# TAFA – nativer Sprachweg und zentrale Steuerung

[English](en/native-only.md) · [Einrichtungsleitfaden](setup-guide.md) · [Android](../android/README.de.md)

## Sprachweg

**TAFA Device Bridge (Android)** erkennt das Rufwort und nimmt die Frage auf → **Home Assistant Assist / TAFA Lokal** → **Whisper (GPU oder CPU)** → HA-Intents oder optional Ollama → **Qwen oder Piper** → **Android-Medienplayer** → optional Bluetooth-Echo.

Das Echo ist bei normalen Gesprächen ein Bluetooth-Medienlautsprecher; **es liefert nicht das Mikrofon**. Eine öffentliche Audio-Domain braucht es dafür nicht. Die getrennte Alexa-MP3-Durchsage benötigt dagegen HTTPS.

## Einrichtung und Modi

1. TAFA über die [Home-Assistant-App](app.md) installieren und **Lokal** oder **Extern** als CPU-Sprachmodus auswählen. Neue Installationen starten in `setup` und laden zunächst keine Modelle.
2. IPs, Wyoming-`stt.*`-Entitäten und optionale Ollama-`conversation.*`-Entität unter **TAFA → Verbindungen** konfigurieren; GPU-Import per JSON ist dort möglich. Wyoming und Ollama müssen vorher in HA eingerichtet sein.
3. Die Assist-Pipeline **TAFA Lokal** mit den drei TAFA-Routern prüfen. Die [signierte Device Bridge](../android/README.de.md) installieren und einen eigenen Nicht-Admin-HA-Benutzer für jedes Tablet verwenden.
4. Optional Bluetooth-Echo koppeln, nativen Player starten, Rufwort wählen und Mikrofonberechtigung erteilen.
5. Unter **TAFA → Geräte & Multiroom** Tablets registrieren und einem Raum zuordnen. Es gibt **keine feste Begrenzung auf vier Räume**.

Der native Android-Mikrofonmodus bietet **Stumm**, **Rufwort** und optional **Immer an**. Eine begrenzte Zahl von Anschlussfragen lässt sich auf dem Tablet einstellen; **unbegrenzte Folgefragen sind nicht die Voreinstellung**. „Immer an“ kann Umgebungsgeräusche als Sprache fehlinterpretieren. Der eigene Bereich **TAFA → Jetzt sprechen** ist **ein separater Browser-Test** mit Transkript/Zeiten und Browser-Audio; er ersetzt weder den Android-Rufwortdienst noch testet er automatisch die Bluetooth-Ausgabe.

## Kamera, Display und Grenzen

**Tablet-Kamera** pro Raum unter **Geräte & Multiroom** ausdrücklich freigeben (Standard: Aus), dann in Device Bridge starten. Bildübertragung ist authentifiziert; der normale Raumnutzer benötigt **keinen Administrator-Token**. Die Vorschau/Bewegungserkennung verwendet aktuelle Einzelbilder und kann irren. [Kamera-Einrichtung](../android/docs/camera-preparation.de.md).

Display-Helligkeit kann mit optionaler Android-Berechtigung gesteuert werden. Ohne privilegierte Geräteverwaltung kann die App den Bildschirm nicht zuverlässig vollständig ein-/ausschalten oder aus Tiefschlaf entsperren. Bei Verbindungsausfall die native Mikrofonanzeige und Geräteberechtigungen prüfen.

Eigene HA-Dashboards, Automatisierungen und andere Assist-Pipelines werden nicht still verändert. Updates der signierten APK erfordern das **gleiche Signaturzertifikat**; eine Debug-APK ersetzt keine vorhandene signierte Installation.
