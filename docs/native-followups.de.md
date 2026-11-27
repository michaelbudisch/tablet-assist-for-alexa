# TAFA: Gezielte Anschlussfragen (0.4.65, Android 1.2.8)

Die native Android-App öffnet nach einer Antwort nur dann erneut das
Mikrofon, wenn Home Assistant im Assist-Event `intent-end` ausdrücklich
`intent_output.continue_conversation=true` liefert.

- **Manuell:** Kein automatischer Smalltalk. Explizite Dialoge wie
  die Internetsuche („Welche Seite soll ich öffnen?“) bleiben möglich.
- **Intelligent (empfohlen):** TAFA wartet nur, wenn der Assistent
  eine konkrete Rückfrage gestellt oder eine Antwort angefordert hat.
  Die Frage des Nutzers allein genügt nicht.
- **Automatisch:** TAFA darf nach jeder Antwort bis zum begrenzten
  Maximum weitere Fragen annehmen.
- **Android-App:** Zusätzlich gilt die lokal eingestellte maximale
  Zahl von Anschlussfragen ohne Rufwort. 0 deaktiviert sie vollständig.
  Die maximale Wartezeit auf den Beginn einer Folgefrage ist separat
  von 2 bis 6 Sekunden einstellbar (Standard 3 Sekunden).
- Nach einem erfolgreichen Abschluss ohne Rückfrage wird sofort zum
  Rufwortmodus zurückgeschaltet. Das End-of-Speech-Fenster der laufenden
  Frage bleibt eine unabhängige Einstellung.
- Das VAD reagiert bei Anschlussfragen zurückhaltender auf Hintergrundgeräusche;
  eine versehentlich aktivierte Anschlussaufnahme ist auf 10 Sekunden begrenzt.

**Wichtig:** Die Kombination aus TAFA-Integration ab 0.4.65 und Android
Device Bridge ab 1.2.8 ist nötig. Bis zum Update des nativen Android-Dienstes
wirkt seine alte, pauschale Anschlussfragen-Logik weiter.
