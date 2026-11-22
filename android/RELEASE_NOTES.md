# HA Jarvis Echo Relay 0.3.0 · Streaming Preview

## Deutsch

- Echtes progressives MP3- und 16-Bit-PCM/WAV-Streaming statt Warten auf die vollständige Datei.
- Android MediaCodec dekodiert MP3 schrittweise; AudioTrack nutzt einen Startpuffer von 600 ms Audio und eine begrenzte PCM-Warteschlange.
- Bluetooth wird mit Nulldaten geprüft, bevor Sprachsamples übergeben werden; die ersten Wörter bleiben erhalten.
- Dateireserve aus derselben HTTP-Antwort nur vor Sprachbeginn. Kein neuer TTS-Auftrag und keine Wiederholung nach teilweise abgespielter Antwort.
- Stopp bricht auch blockierte Netzwerkantworten ab. Diagnose enthält Modus, erste Bytes/PCM-Übergabe und Nachpufferungen.
- Oberfläche, DE/EN, Token-Scan, Zugangsdaten, HTTP-Freigabe und optionaler Keepalive bleiben erhalten.

Die APK über die vorhandene App installieren. Die App-ID bleibt `de.jarvis.audio`; Adresse und Token bleiben erhalten. Signierter, nicht debuggbarer Release-Build mit dem bisherigen lokalen Testschlüssel für Update-Kompatibilität. Keine privaten Schlüssel enthalten. Die App benötigt weiterhin den dokumentierten nativen Audio-Helfervertrag.

JVM-Tests und Android-Lint sind bestanden. Im isolierten Android-Emulator wurden echte verzögerte HTTP-Antworten mit MP3 (24 kHz mono und 44,1 kHz stereo) sowie Streaming-WAV geprüft: Wiedergabebeginn vor vollständigem Empfang und bytegleiche PCM-Daten gegenüber vollständiger Dekodierung. Hinzu kommen native Netzwerkabbrüche, fehlendes Bluetooth und die bisherigen DE/EN-UI-Tests. Die tatsächliche Latenz und Keepalive-Wirkung auf Tablet/Echo erfordern Hardwaretests. Der 600-ms-Wert bezeichnet gepufferte Audiodauer, keine zugesicherte Startzeit. Antwortgenerierung und vorgeschaltete Puffer bleiben außerhalb der App.

## English

- Progressive MP3 and 16-bit PCM/WAV streaming starts before the complete response has downloaded.
- Android MediaCodec decodes MP3 incrementally; AudioTrack uses a 600 ms audio startup target and a bounded PCM queue.
- Bluetooth is primed with zeros before speech submission, preserving the beginning of the answer.
- Same-response file fallback is allowed only before speech, with no new TTS request and no replay after partial playback.
- Stop interrupts blocked network responses. Diagnostics report mode, first bytes/PCM submission and rebuffering.
- Existing interface, DE/EN, token scan, credentials, local HTTP consent and optional keepalive remain available.

Install over the existing app to retain credentials. The application ID remains `de.jarvis.audio`. This non-debuggable release APK uses the same local test signing key as earlier builds for update compatibility. Private signing keys are not included. A controller implementing the documented native audio helper contract is still required.

JVM tests and Android lint passed. Real delayed chunked HTTP responses were tested on an isolated Android emulator using MP3 (24 kHz mono and 44.1 kHz stereo) and streaming WAV: playback began before response completion and every decoded PCM byte matched complete decoding. Native HTTP cancellation, absent Bluetooth and existing German/English UI checks were also verified. Actual tablet/Echo latency and keepalive behavior need hardware testing. The 600 ms value is buffered audio duration, not a promised wall-clock start time. Answer generation and upstream buffering remain outside the app.
