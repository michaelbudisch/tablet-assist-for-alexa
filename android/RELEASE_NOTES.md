# HA Jarvis Echo Relay 0.5.0 · Camera and Vision Preview

## Deutsch

Front-/Rückkamera als authentifizierte HA-Bildquelle mit ungefähr einem neuen JPEG alle zwei Sekunden, eigenem Kamera-Vordergrunddienst und Stopp-Benachrichtigung. Optionaler Bildbewegungssensor, Bilder im Arbeitsspeicher, Sitzungsschutz und Ablauf alter Bilder nach 15 Sekunden ohne Nachschub. Kein automatischer Start nach Neustart.

Passender HA-Empfänger Jarvis Tablet Audio 1.4.0 mit Kameraauswahl und lokalen Vision-Aktionen. Beispiele: „Was ist draußen los?“, „Was siehst du?“ und „Was halte ich in der Hand?“. Der bestehende GPU Worker 1.6.0 wird genutzt; die App benötigt keinen weiteren produktiven Docker-Dienst. Audiostreaming, Bluetooth-Prüfung, Keepalive, DE/EN und Zugangsdaten bleiben erhalten.

Über die vorhandene App installieren, dann **Kameraeinstellungen öffnen → Kamera für HA starten**. Die Kopplung verwendet den gespeicherten HA-Administrator-Token. Andere Installationen benötigen zuerst den passenden HA-Empfänger und ein installiertes Visionmodell. [Anleitung](https://github.com/michaelbudisch/tablet-assist-for-alexa/blob/main/android/docs/camera-preparation.md).

25 JVM-Tests, Android-Lint, native Kamera-/Hintergrund-/HTTP-, Oberflächen- und Streamingtests sowie isolierte echte HA-Empfänger-/Routingtests sind bestanden. Der signierte Release-Build hat den Hintergrund-/Uploadtest bestanden. Das Display-aus-Verhalten benötigt weiterhin den Test auf dem Zieltablet. Bewegung vergleicht Pixel; Vision beschreibt Einzelbilder und kann irren. Dies ist kein Video mit voller Bildrate.

## English

Explicit-start camera foreground delivery pushes bounded, upright JPEGs to the authenticated HA receiver about every two seconds. A separate notification stops it; audio remains independent. Optional image movement, memory-only images, session invalidation and a 15-second freshness limit are included. The matching HA integration selects tablet/outdoor/door images and calls the existing local vision worker for explicit questions/actions.

Install over the previous app to retain credentials. Application ID `de.jarvis.audio`; non-debuggable release signed with the same previous local test key. No private keys included. JVM, lint, native Android camera/background/HTTP/UI/audio and real-HA receiver/routing checks passed. Actual tablet battery/screen-off behavior still needs hardware validation. See the linked setup guide.
