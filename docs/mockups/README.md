# Mockups — UX-Referenz, NICHT für Claude-Auto-Read

`v1-target-ui.html` ist 1873 Zeilen / 104 KB und nur menschlich gedacht
(Browser-Demo). **Claude soll das nicht lesen, außer es wird explizit
darauf verwiesen.** Lesen kostet ~25k Tokens und liefert kaum Information,
die nicht schon in den ADRs steht.

Wenn Layout-Details aus dem Mockup gebraucht werden:
- Erst klären welche Sektion → mit `Read offset/limit` gezielt laden.
- Niemals den ganzen File einlesen.
