# TAFA Visualstream – Gerätezustellung

Ab TAFA 0.4.64 empfangen normale Dashboard-Ansichten und der Ambientmodus Sprachantworten über den authentifizierten WebSocket-Befehl `tablet_assist_for_alexa/visual_subscribe`. Die Gerätezuordnung kommt ausschließlich über `tablet_assist_for_alexa/visual_identity`. Direkte Frontend-Abos auf `tafa_assist_response` sind nicht mehr erforderlich.

- Ein Raum-Benutzer mit genau einem zugeordneten Tablet erhält ausschließlich dessen Antworten.
- Bei mehreren Geräten sowie bei Administrator-Logins erfolgt **keine automatische Zuordnung**. Der lokale Bildschirm muss explizit über den Gerätestatus-Sensor (Browser-Einstellung `tafa.dashboard.local_voice_sensor.v1`) gebunden sein. Die Identität wird gegen die vom Backend autorisierten Geräte geprüft.
- Ist kein passendes Gerät zugeordnet, bleibt der Bildschirm passiv. Die Antwort wird nicht stattdessen aus einem anderen Raum angezeigt.
- Die native TAFA Device Bridge steuert Rufwort und Anschlussfragen selbst; der Visualstream startet kein Mikrofon.
- Das Frontend verwendet keinen Fallback auf Administrator-HA-Ereignis-Abos. Bei fehlender Berechtigung wird die Antwort nicht angezeigt; der Fehler wird in der Browserkonsole protokolliert.
- Die auslieferbare Integration und das `tafa_app/bundle` verwenden denselben Frontendstand.

## Bestandsanlagen und Automatisierungen

Ältere Android-Wake-Pilot-Automatisierungen mit `jarvis_android_wakeword` können noch vorhanden sein. Diese gehören zur älteren Browser-Sprachsteuerung, nicht zum nativen TAFA-Gesprächspfad. Vor Deaktivierung ist zu prüfen, ob andere Automatisierungen auf ihr weitergeleitetes Ereignis `jarvis_android_wakeword_routed` reagieren.

Proaktive Infobox-Ereignisse wie `jarvis_infobox_show` sind **nicht** mit dem Sprachantwort-Stream gleichzusetzen. Sie dürfen ohne eigene berechtigungsgeprüfte Zustellung nicht pauschal auf `tafa_assist_response` umgestellt werden.

Nach einem Update die Browser-WebView neu laden, damit die neue ESM-Version (0.4.64) verwendet wird. Eine tatsächliche Sprachprobe bleibt für den Ende-zu-Ende-Test erforderlich.
