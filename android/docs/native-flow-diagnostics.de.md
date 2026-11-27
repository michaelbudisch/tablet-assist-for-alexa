# Native Ablaufdiagnose · TAFA Device Bridge 1.2.6

Die Diagnose wird ausschließlich auf dem Tablet erfasst und in der nativen App angezeigt. Die vorhandene HA-Assist-Pipeline und der GPU Worker liefern weiterhin Sprache und Antworten; für die Messung werden keine zusätzliche Automation, kein Dashboard und keine neuen Serverabfragen eingerichtet.

## Starten
1. Die gleich signierte APK über die bestehende App installieren, ohne vorherige Deinstallation.
2. **Einstellungen → Hilfe & Diagnose → Nativer Sprachablauf** öffnen. **Zeitmetadaten lokal mitschreiben** ist standardmäßig an.
3. Den Player verbinden und die gewünschte Mikrofonart aktivieren. Eine Frage mit Rufwort stellen oder **Jetzt sprechen** verwenden.
4. Die Antwort ausspielen lassen. Anschließend die Anfrage in der Diagnose auswählen.
5. **Diagnose-JSON kopieren** oder **teilen** übergibt die Zeitmetadaten als Text. Es erfolgt kein automatischer Versand.

## Welche Zahl vergleichen?
**Sprachende → Android-Ausgabe** ist die wichtigste Antwortlatenz. Sie enthält auch die konfigurierte Sprechendepause. **Auslöser → Android-Ausgabe** enthält zusätzlich die Aufnahmedauer der Frage und bei Rufwortbetrieb den Wechsel vom Rufwort-Recorder zu Assist.

Der Auslöser ist die lokale Rufworterkennung, der Beginn einer manuellen Assist-Anfrage oder die bestätigte lokale Aktivität im Modus Immer an. Es ist nicht der akustische Beginn des gesprochenen Rufworts. Lokale Sprachaktivität und das letzte Sprachframe werden über den vorhandenen Pegeldetektor in 20-ms-Frames bestimmt; dies ist keine inhaltliche Spracherkennung.

| Abschnitt | Messgrenze auf dem Tablet |
| --- | --- |
| Mikrofonübergabe | Erkannter Auslöser bis AudioRecord-Aufnahme |
| Sprechpause | Letzter lokaler Sprachframe bis Aufnahmeende |
| Assist-Aufbau | Native Anfrage bis empfangenem STT-Start |
| Upload | Erste PCM-Übergabe an WebSocket bis Endemarkierung |
| STT-Nachlauf | PCM-Endemarkierung bis empfangenem STT-Ergebnis |
| Agent | Empfang der Assist-Ereignisse intent-start bis intent-end |
| TTS-Bereitstellung | Empfang von tts-start bis tts-end / Audio-URL |
| Auftragsübergabe | Submit-Start bis lokaler Player den Auftrag erhält |
| Audioabruf | Lokaler HTTP-Abruf bis erstes Audiobyte |
| Decoder / Puffer | Erstes Byte, erstes PCM, freigegebener Startpuffer |
| Ausgang | Bestätigte Route, PCM-Übergabe, Android-Wiedergabefortschritt |
| Abschluss | Geleerte Android-Ausgabe bis Assist-Sitzungsabschluss |

Die Abschnitte können überlappen und dürfen nicht summiert werden. Eine nicht vorhandene Messgrenze erscheint als **—**, nicht als geschätzte Null.

## Ausgabe und Messgrenzen
Eine PCM-Übergabe an AudioTrack ist noch keine bestätigte Wiedergabe. Der Streamingpfad beobachtet deshalb, ob der Playback-Head die ersten Antwortframes nach den stummen Routenprüfungsframes überschreitet. Der Datei-Fallback verwendet den Fortschritt der MediaPlayer-Position nach der Lautstärkefreigabe; dessen vorhandener Routentimer beobachtet alle 100 ms. Die Messqualität steht im Export unter OUTPUT_QUALITY.

Dies misst den Android-Ausgabepfad. Zusätzliche akustische Verzögerung des Echo/Bluetooth-Lautsprechers und führende Stille der erzeugten Audiodatei sind damit nicht bestimmt. Die Messung behauptet keinen akustischen Mikrofon-zu-Lautsprecher-Rundlauf.

Serverphasen basieren auf dem Eintreffen der Assist-Ereignisse an derselben Tablet-Uhr. Sie enthalten Transport und Serverplanung; reine Whisper-/LLM-/TTS-GPU-Rechenzeit und Netzwerkzeit lassen sich daraus nicht getrennt bestimmen. tts-end bezeichnet die bereitgestellte Audio-URL und bei Streaming nicht notwendigerweise das Ende der gesamten Audiosynthese. Der GPU Worker wird dafür nicht verändert.

Der tatsächliche Player wird anhand der vom Submit zurückgegebenen Auftrags-ID zugeordnet. Wenn Audio schon vor der HTTP-Antwort anläuft, werden seine ursprünglichen lokalen Zeitpunkte nachträglich zugeordnet. Andere Durchsagen werden nicht als Antwort dieser Anfrage gezählt. Der bestehende 650-ms-Statusabgleich wird nicht als Wiedergabestart verwendet.

## Vergleichbare Tests
Für einen Vergleich dieselbe Audioausgabe, dieselbe Sprechpause und dieselbe Frage verwenden, z. B. „Erkläre in einem Satz, was ein Regenbogen ist“. Rufwort, manuelle Anfrage, Folgefrage und Immer an werden getrennt ausgewertet, ebenso Ausgang, Player und Sprechpause.

Den ersten Lauf nach Rechner-/Modellstart getrennt exportieren. Für warme Läufe den Verlauf danach löschen und etwa 10–20 vergleichbare Fragen ausführen. P50/P95 gelten nur für erfolgreiche Läufe mit beobachtetem Ausgabefortschritt; die Stichprobengröße n steht dabei. Fehler, Abbrüche und unterbrochene Messungen bleiben im Verlauf sichtbar. Bei kleinen Stichproben sind die Quantile nur orientierend.

## Speicherung und Aufwand
Höchstens 20 Anfragen und 32 interne Audioaufträge werden gehalten. Gespeichert werden relative Zeiten, Auslöserart, Ergebnis, Ausgang und begrenzte technische Zähler. Keine Audiodaten, Frage-/Antworttexte, Serveradressen, Tokens oder HA-Auftrags-IDs werden exportiert.

Messpunkte verwenden die monotone Tablet-Uhr. Es gibt keine zusätzlichen Audio-Pausen und keine zusätzliche Server-Telemetrie. Metadaten werden bei Beginn/Ende und beim vorhandenen Hintergrund-Checkpoint koalesziert außerhalb des Audiothreads gespeichert; nicht pro Audioframe. **Mitschreiben aus** beendet nur die Messung, nicht die Unterhaltung. **Zeitverlauf löschen** entfernt auch die Zuordnung laufender Messungen; spätere Callbacks lassen sie nicht wieder erscheinen.

## Quellen der Schnittstellen
- [Home Assistant Assist-Pipeline-Ereignisse](https://contributors.home-assistant.io/core/internals/assist-pipelines/)
- [Android AudioTrack Playback-Head](https://developer.android.com/reference/android/media/AudioTrack#getPlaybackHeadPosition())

Die Emulatoransichten in den lokalen Diagnoseberichten verwenden ausdrücklich synthetische Testdaten, keine Messungen deines Tablets.
