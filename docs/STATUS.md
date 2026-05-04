# STATUS — pem-ec-designer

> Read-on-demand. CLAUDE.md verweist hierher.
> Halte diese Datei aktuell beim Session-Ende.

## Stand 2026-05-02 · v0.0.1 (unreleased: +geometry +gdl)

| Bereich | Stand |
|---|---|
| ADR-001 Framework | ✓ PyQt6 + pyvistaqt + build123d |
| ADR-002 Library | ✓ Pydantic v2, per-cat JSON, BibTeX, Hierarchical IDs |
| ADR-003 Qt-Binding | ✓ PySide6 (LGPL) — formalisiert, was im pyproject schon stand |
| Python-Scaffold | ✓ `src/pem_ec_designer/` mit foundation/schema/materials/**geometry** |
| Library | ✓ 5 Membranen + **8 GDL** + **2 Anode-CL** + 2 Materials + **18 BibTeX** (inkl. 2 books, 2 GDL-DOI-Papers) |
| Schema-E1 | ✓ `Component.material` optional · `manufacturer` + `cross_references` auf Component-Ebene · `GasDiffusionLayer` mit 14 Feldern · neuer `CrossReference` BaseModel · ID-Pattern erlaubt Underscore (für `anode_cl.*` u.a.) |
| Units | ✓ +21 Engineering-Units (areal density, ρ-Varianten, λ thermisch, Zeit, Winkel, dimensionslose Brüche, **mg/cm² Katalysator-Loading**) |
| Geometry | ✓ `build_extruded()` (kreis/quadrat/rechteck) + `build_membrane` + `build_flow_field` (straight_parallel). STEP-Export verifiziert. |
| Tests | ✓ **88/88** lokal (vorher 85; +1 mg/cm² round-trip, +1 mg/cm² equivalence, +1 underscored-ID) |
| UI-Stack-Smoke | ✓ PySide6 6.11 + pyvistaqt 0.11 + VTK rendert Membrane-STL → PNG. Findings in `docs/UI-LAUNCH-NOTES.md`. |
| UI v0 | ✓ `python -m pem_ec_designer` öffnet MainWindow: Library-Sidebar + VTK-Viewer. Klick → Generator → Mesh. Screenshot 115 KB. |
| Repo | private · [Tools00/pem-ec-designer](https://github.com/Tools00/pem-ec-designer) |

## Offene Pfade (User wählt)

| | Pfad | Was |
|---|---|---|
| **A** | Specs erweitern | gdl/bpp/anode_cl/flow_field je 2-5 Items mit echten BibTeX-Quellen. **Stand:** GDL **vollständig** (Toray TGP-H-030/-060/-090/-120, SIGRACET 22 BB / 28 BC / 36 BB / 39 BB). Anode CL: 2 Specs aus Bernt 2016 (IrO₂/TiO₂, 2.0 + 1.46 mg_Ir/cm²). Nächster sinnvoller Schritt: Cathode CL aus Bernt 2020 (Pt-Loadings) oder BPP (POCO/Schunk Datasheets nötig) oder Materials erweitern (IrO₂ als Material aus Carmo 2013 Review). |
| **B'''** | weitere FF-Patterns | serpentine (Sweep), interdigitated |
| **C+** | UI-Politur | Material-Card seitlich, STEP-Export-Button, Footprint-Form-Filter, **Maßstabs-Lineal im Viewer (mm)**, Edge-Toggle, Z-Faktor frei wählbar (10/100/1000) |
| **E** | Stack-Composer | Membrane + 2× FF + 2× Endplate stapeln, ADR-005 ziehen |
| **D** | pause | nichts tun |

## Bekannte TODOs

- ~~ADR-003 Qt-Binding~~ ✓ entschieden (PySide6/LGPL)
- ADR-004 Geometry-Generator-Binding — `build_extruded` deckt 3 Kategorien, FF separat → Pattern bestätigt; ADR optional bis Stack-Composer kommt
- Produkt-Lizenz-System (FlexLM o.ä.) — out of scope, eigenes ADR wenn jemals nötig
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
