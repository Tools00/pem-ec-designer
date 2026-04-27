# CLAUDE.md — pem-ec-designer

**Manual für Claude. Klein halten — wird bei jeder Session gelesen.**

## Bootstrap

1. `cat docs/STATUS.md` → aktueller Stand, offene Pfade, nächste Optionen.
2. `git log --oneline -5` → was zuletzt passiert ist.
3. Frag User welcher Pfad — antworte visuell (Tabelle/HTML), nicht in Prosa.

## Verhaltensregeln

- **Visuell statt Prosa-Listen** bei ≥2 Optionen. Tabellen, Karten, HTML.
- **Senior-Mindset:** widersprich, wenn Annahmen falsch sind. Alternative immer mit.
- **Strict-Quellen:** jeder Wert in `library/` braucht BibTeX-Key. Kein Erfinden — `null` wenn unklar.
- **Layer-Trennung:** kein Qt-Import in `physics/`, `schema/`, `foundation/`. CI prüft.
- **Inkrementell:** 5 Specs prüfen → skalieren. Kein Big-Bang.
- **Kein Commit ohne explizites OK** vom User.

## Token-Hygiene (wichtig)

- **Nicht** auto-lesen: `docs/decisions/*.html`, `docs/mockups/*.html`, `library/schema.json`
  → user-facing oder generiert; nur lesen wenn explizit gefragt.
- Bei großen Files: `Read` mit `offset/limit` statt komplett.
- Recherche-/Such-Aufgaben → Subagent (isolierter Context).
- Lange Sessions: nach ~30 Nachrichten neue Session vorschlagen.

## Kanonische Quellen

- `docs/STATUS.md` — wo wir stehen + offene Pfade
- `docs/adr/001-framework-choice.md` — Stack
- `docs/adr/002-library-architecture.md` — Library-Layout
- `CHANGELOG.md` — Versions-Log
