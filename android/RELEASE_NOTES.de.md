# HA Jarvis Echo Relay 0.5.0 · Kamera- und Vision-Vorschau

[English](RELEASE_NOTES.md) | **Deutsch** · [Projektübersicht](../README.de.md)

Front-/Rückkamera als authentifizierte HA-Bildquelle mit ungefähr einem neuen JPEG alle zwei Sekunden, eigenem Kamera-Vordergrunddienst und Stopp-Benachrichtigung. Optionaler Bildbewegungssensor, Bilder im Arbeitsspeicher, Sitzungsschutz und Ablauf alter Bilder nach 15 Sekunden ohne Nachschub. Kein automatischer Start nach Neustart.

Passender HA-Empfänger Jarvis Tablet Audio 1.4.0 mit Kameraauswahl und lokalen Vision-Aktionen. Beispiele: „Was ist draußen los?“, „Was siehst du?“ und „Was halte ich in der Hand?“. Der bestehende GPU Worker 1.6.0 wird genutzt; die App benötigt keinen weiteren produktiven Docker-Dienst. Audiostreaming, Bluetooth-Prüfung, Keepalive, DE/EN und Zugangsdaten bleiben erhalten.

Über die vorhandene App installieren, dann **Kameraeinstellungen öffnen → Kamera für HA starten**. Die Kopplung verwendet den gespeicherten HA-Administrator-Token. Andere Installationen benötigen zuerst den passenden HA-Empfänger und ein installiertes Visionmodell. [Anleitung](docs/camera-preparation.de.md).

25 JVM-Tests, Android-Lint, native Kamera-/Hintergrund-/HTTP-, Oberflächen- und Streamingtests sowie isolierte echte HA-Empfänger-/Routingtests sind bestanden. Der signierte Release-Build hat den Hintergrund-/Uploadtest bestanden. Das Display-aus-Verhalten benötigt weiterhin den Test auf dem Zieltablet. Bewegung vergleicht Pixel; Vision beschreibt Einzelbilder und kann irren. Dies ist kein Video mit voller Bildrate.
