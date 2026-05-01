# STATUS — pem-ec-designer

> Read-on-demand. CLAUDE.md verweist hierher.
> Halte diese Datei aktuell beim Session-Ende.

## Stand 2026-04-29 · v0.0.1 (unreleased: +geometry)

| Bereich | Stand |
|---|---|
| ADR-001 Framework | ✓ PyQt6 + pyvistaqt + build123d |
| ADR-002 Library | ✓ Pydantic v2, per-cat JSON, BibTeX, Hierarchical IDs |
| Python-Scaffold | ✓ `src/pem_ec_designer/` mit foundation/schema/materials/**geometry** |
| Library | ✓ 5 Membranen + 2 Materials + 11 BibTeX |
| Geometry | ✓ generischer `build_extruded()` (kreis/quadrat/rechteck) + `build_membrane`-Wrapper. STEP-Export verifiziert. |
| Tests | ✓ 54/54 lokal (inkl. rechteckiger Pfad + Error-Paths) |
| Repo | private · [Tools00/pem-ec-designer](https://github.com/Tools00/pem-ec-designer) |

## Offene Pfade (User wählt)

| | Pfad | Was |
|---|---|---|
| **A** | Specs erweitern | gdl/bpp/anode_cl/... je 2-5 Items mit echten BibTeX-Quellen — füttert den vorhandenen generischen Builder |
| **B''** | Flow-Field-Generator | erste **nicht-extrudierte** Geometrie (Kanäle, Stege) — neues Pattern, eigener Generator nötig |
| **C** | UI-Skelett | PyQt6-MainWindow + pyvistaqt zeigt geladene STEPs |
| **D** | pause | nichts tun |

## Bekannte TODOs

- ADR-003 Lizenz (PyQt6 GPL → PySide6 LGPL?) — Late binding
- ADR-004 Geometry-Generator-Binding — nach 5 Generatoren entscheiden
- ADR-005 Stack-Composition — nach Library + Geometry
- 55 weitere Komponenten-Specs (Wide-60 — inkrementell)
- Cost-Felder durchgängig `null` → Preis-Recherche TODO

## Scope-Grenzen (verbindlich)

**Drin:** Desktop-App · Python+PyQt · Komponenten-Library · build123d-CAD · 0D-Physik
**Draußen v1.0:** Multi-User · Web-UI · CFD · 1D-Fluid · Lizenz-System
**Niemals:** Werte ohne Paper-Quelle

## Bootstrap-Sequenz

```bash
cd path/to/Simulation-tools/pem-ec-designer
claude --continue              # mit Historie
# oder
claude                         # frisch — CLAUDE.md genug
PYTHONPATH=src pytest -q       # 45 grüne Tests verifizieren
gh run list --limit 3          # CI-Stand
open docs/decisions/000-roadmap.html   # visueller Stand
```

## Nicht in Auto-Read laden

- `docs/decisions/*.html` — UX-Karten für User, nicht für Claude
- `docs/mockups/*.html` — Design-Referenz (sehr groß), nur bei Bedarf
- `library/schema.json` — auto-generiert, CI-only

## Decision-Index (read on demand)

- 000-roadmap · Status · `docs/decisions/000-roadmap.html`
- 001-library-scope · 4 Library-Fragen · entschieden
- 002-framework-adr · 8 Pflichtfragen · entschieden
- 003-adr-conflicts · 3 Konflikte · gelöst
- 004-library-architecture · 6 Punkte · alle Defaults
- 005-github-deploy · 5 Stufen · auf Stage 3
- 006-session-handoff · diese Erklärung
