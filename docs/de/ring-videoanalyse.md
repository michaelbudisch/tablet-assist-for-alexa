# Ring-Videoframes für Jarvis / TAFA (Entwicklervorschau)

Die Ring-Entitäten `camera.haustur_letzte_aufnahme` und `camera.vorderseite_letzte_aufnahme` liefern eine signierte MP4-URL. Ein normaler Aufruf von `describe_camera` im Modus `scene` verarbeitet weiterhin **nur ein Einzelbild**. Der neue Modus `ring_video` untersucht bis zu vier Zeitpunkte der letzten MP4-Aufzeichnung.

## Ablauf
1. Home Assistant wartet, bis `Letzte Aktivität` und `Letzte Aufzeichnung` zum selben Ereignis passen.
2. Die bereits vorhandene gemeinsame KI-Warteschlange ruft `jarvis_tablet_audio.describe_camera` auf.
3. Mit `mode: ring_video` wird die signierte Ring-MP4 (maximal 20 MiB) heruntergeladen. Nur Ring-Downloadhosts werden akzeptiert.
4. Ein lokal vorhandenes `ffmpeg` extrahiert ungefähr die Sekunden 3, 8, 13 und 18. Kürzere Clips ergeben entsprechend weniger Bilder.
5. Vier beschriftete Standbilder werden als 2×2-Montage von Qwen3-VL im bestehenden `scene`-Modus bewertet. Das ist **keine echte kontinuierliche Videoanalyse**.
6. Die Beschreibung geht wie bisher an `jarvis_infobox_update`; die bestehende Post-/Paket-Textregel und der TAFA-KI-Verlauf bleiben aktiv.

## Installation
- Die Änderungen in `homeassistant/custom_components/jarvis_tablet_audio/` nach `/config/custom_components/jarvis_tablet_audio/` übernehmen. **Vorher sichern**, nicht einzelne Dateien einer inkompatiblen Version mischen.
- `ffmpeg` muss **im Home-Assistant-Core-Container** als ausführbares Programm vorhanden sein (`ffmpeg` im PATH); ein externer ffmpeg-Container reicht nicht.
- Home Assistant **neu starten**, damit die geänderte Python-Service-Schnittstelle geladen wird.
- Erst danach in `script.ring_ki_bildanalyse_seriell` die Aktion `jarvis_tablet_audio.describe_camera` von `mode: scene` auf **`mode: ring_video`** stellen. Das ist eine einzige Änderung im vorhandenen Script; die Warteschlange bleibt erhalten.
- Für einen manuellen Funktionstest `jarvis_tablet_audio.describe_camera` mit `source: door` bzw. `source: outside` und `mode: ring_video` ausführen. Die Antwort enthält `frames_analyzed` und `limitation`.
- Danach erneut einen echten Ring-Test durchführen, Erkennung im Dashboard unter *Kameras → KI-Erkennungsverlauf* prüfen.

## Grenzen und Sicherheit
- Die Ring-Cloud darf ein Ereignis weiterhin verzögert melden. Kurzlebige MP4-Links können verfallen.
- Nur die aktuelle letzte Aufnahme wird betrachtet; bei mehreren aufeinanderfolgenden Ereignissen muss die bereits vorhandene Zeitstempelprüfung einen Wechsel der Aufnahme abfangen.
- Die Aufnahme wird für die ffmpeg-Verarbeitung kurz in einer privaten temporären Datei gehalten und unmittelbar gelöscht; keine dauerhaften Videos, Bilder oder URL-Tokens protokollieren.
- Pro Ereignis erfolgt höchstens eine Vier-Frame-Montage, **keine Personenidentifikation**.
- Nicht erkannte Pakete oder Personen sind möglich, besonders bei Dunkelheit, Bildunschärfe oder wenn die Person außerhalb der vier Zeitpunkte zu sehen ist.
- Aufzeichnung und Bildanalyse nur unter Beachtung der Privatsphäre betroffener Personen aktivieren.

## Rückfall
Falls ffmpeg fehlt oder die MP4 nicht geladen werden kann, wird die Anforderung als Fehler gemeldet; sie darf **nicht stillschweigend** als Vier-Frame-Erfolg gelten. Den Aufruf wieder auf `mode: scene` zurückstellen, um die bisherige Einzelbild-Erkennung zu nutzen. Die Echo-Durchsage und die 30-Minuten-Sperre werden von dieser Änderung nicht verändert.
