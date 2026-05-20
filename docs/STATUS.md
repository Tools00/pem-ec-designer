# STATUS — pem-ec-designer

> Read-on-demand. CLAUDE.md verweist hierher.
> Halte diese Datei aktuell beim Session-Ende.

## Stand 2026-05-19 · **v0.1.0 released** (MIT, tag pushed)

| Bereich | Stand |
|---|---|
| ADR-001 Framework | ✓ PyQt6 + pyvistaqt + build123d |
| ADR-002 Library | ✓ Pydantic v2, per-cat JSON, BibTeX, Hierarchical IDs |
| ADR-003 Qt-Binding | ✓ PySide6 (LGPL) — formalisiert, was im pyproject schon stand |
| **ADR-005 LCOH** | ✓ Annuitäten-Modell · Schmidt-2017-Defaults · η_LHV-getrieben |
| **ADR-006 Stack-Composer** | ✓ 9 Library-Filter-Dropdowns · σ-cut-off 100 S/m für membrane materials |
| **UI Single-Page** | ✓ Header (Title + Validation-Badge) · §1 Stack Design (Composer + collapsible 3D-Viewer) · §2 Operating **+ Design-j-Slider** · §3 Results **mit Design-Marker** · §4 Economics · §5 Export (CSV + BibTeX live) |
| **Export-Layer** | ✓ `export/csv_export.py` + `export/bibtex_export.py` + `assembly/source_collector.py`. CSV mit self-doc-Header; BibTeX-Subset enthält nur zitierte Keys. |
| Python-Scaffold | ✓ `src/pem_ec_designer/` mit foundation/schema/materials/**geometry** |
| Library | ✓ 5 Membranen + **8 GDL** + **2 Anode-CL** + **2 Cathode-CL** + **1 BPP** + **3 Materials** + **20 BibTeX** (inkl. 2 books, 2 GDL-DOI-Papers, 1 Cathode-CL-Paper, 1 POCO-Datasheet) |
| Schema-E1 | ✓ `Component.material` optional · `manufacturer` + `cross_references` auf Component-Ebene · `GasDiffusionLayer` mit 14 Feldern · neuer `CrossReference` BaseModel · ID-Pattern erlaubt Underscore (für `anode_cl.*` u.a.) |
| Units | ✓ +21 Engineering-Units (areal density, ρ-Varianten, λ thermisch, Zeit, Winkel, dimensionslose Brüche, **mg/cm² Katalysator-Loading**) |
| Geometry | ✓ `build_extruded()` (kreis/quadrat/rechteck) + `build_membrane` + `build_flow_field` (straight_parallel). STEP-Export verifiziert. |
| Tests | ✓ **226/226** lokal (+11 persistence Ini-roundtrip, +3 onboarding-banner) |
| **Physics-Layer** | ✓ **`physics/` aktiv** — `thermodynamics.E_rev(T,p)`, `kinetics.butler_volmer_overpotential`, `ohmic.OhmicContribution`/`total_asr`, `polarization.cell_voltage`/`polarisation_curve`. Modell per **ADR-004** (0D · steady · isotherm · BV+ASR). Bernt-2016 + Carmo-2013 Validation-Anchor erfüllt. |
| **Economics-Layer** | ✓ **`physics/efficiency.py` + `physics/lcoh.py`** — `lhv_efficiency(V)`, `levelised_cost_of_hydrogen(η, LCOHInputs)`. ADR-005 mit Schmidt-2017-Anker (3.71 €/kg @ η=0.65, 50 €/MWh, 1100 €/kW). |
| UI-Stack-Smoke | ✓ PySide6 6.11 + pyvistaqt 0.11 + VTK rendert Membrane-STL → PNG. Findings in `docs/UI-LAUNCH-NOTES.md`. |
| UI v0 | ✓ `python -m pem_ec_designer` öffnet MainWindow mit **2 Tabs**: „Components" (Library-Sidebar + VTK-Viewer) und **„Simulation" (StackComposer mit 9 Dropdowns + T/p-Slider + V–I-Kurve + Loss-Waterfall + LCOH-Panel mit CapEx/Strompreis-Slidern, live-replot)**. Screenshots in `/tmp/pem_ec_designer_simulation.png`. |
| Assembly | ✓ `assembly/stack.py:build_stack(...)` — Component/Material → `CellKinetics`/`OhmicContribution`/`OperatingPoint`. Skipped-Layer-Diagnostics. 4 Tests. |
| Repo | public · [Tools00/pem-ec-designer](https://github.com/Tools00/pem-ec-designer) |

## Offene Pfade (User wählt)

| | Pfad | Was |
|---|---|---|
| ✓ F | ~~Simulations-UI~~ | **DONE** — Tab „Simulation" mit T/p-Slidern, V–I-Kurve + Loss-Waterfall. V(1 A/cm²) ≈ 1.61 V aus echtem Library-Stack. `scripts/smoke_simulation_tab.py` als Evidence. |
| ✓ H | ~~Assembly-Layer~~ | **DONE** — `assembly/stack.py:build_stack(...)`. Bridge Component/Material → physics-Inputs. Skipped-Layer-Diagnostics in StatusBar. |
| ✓ G | ~~LCOH-Modul~~ | **DONE** — `physics/efficiency.py` + `physics/lcoh.py` + ADR-005 + `ui/economics_panel.py`. Schmidt-2017-Anker erfüllt (3.71 €/kg @ η=0.65). Sliders live unter Simulation-Tab. |
| ✓ I | ~~Stack-Composer~~ | **DONE** — `assembly/library_filter.py` (8 pure filters) + `ui/stack_composer.py` (9 ComboBoxes) + ADR-006. Defaults reproduzieren v0-Hardcoded-Stack. |
| ✓ C+1 | ~~UX-Politur Teil 1~~ | **DONE** — Single-Page-Scroll mit 5 Sektionen + `ui/source_tooltip.py` + `ui/validation_badge.py` (Bernt-2016-Anker). Click-to-explain Dialog. |
| ✓ C+2a | ~~Design-j + CSV/BibTeX-Export~~ | **DONE** — Design-j-Slider (0.1–4 A/cm²) mit Marker-Sync, CSV-Export mit Self-Doc-Header, BibTeX-Subset-Export (genutzte Quellen). |
| ✓ C+2b | ~~QSettings + Shortcuts + Onboarding~~ | **DONE** — `ui/persistence.py` (stack/op/lcoh/window/ui Keys per §9), `Cmd+E/D/R/?` Shortcuts, dismissible Banner mit `ui.onboardingSeen`-Persist. |
| ✓ STEP-Export | ~~Stack-Geometrie-Aggregation~~ **DONE** — ADR-008 + `geometry/stack_assembly.py` (pure, 7-Layer fixed order, per-Layer Footprint, true SI Z-Achse) + `_on_export_step` Handler + Sidecar `<name>.layers.json` mit Material-Mapping. 5 neue Tests. |
| **★ Release v0.1** | UX-VISION §14 N+5 — CHANGELOG aufräumen, README mit Screenshot, LICENSE-Diskussion, `git tag v0.1.0`. |
| A | Specs erweitern | GDL **vollständig** (8). CL: 4 (2 Anode + 2 Cathode). BPP: 1. Endplate/Gasket/FF noch offen. **Niedrige Priorität**. |
| C+ | UI-Politur (alt) | Material-Card, STEP-Export-Button, Skala im 3D-Viewer. **Niedrige Priorität**. |
| D | pause | nichts tun |

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

## UX-Nordstern

`docs/UX-VISION.md` — bindendes UI/UX-Konzept für v1.0. Lesepflicht für jede UI-Session.
Kernaussage: Tabs → scrollbare Single-Page-Notebook mit 5 Sektionen (§1 Stack Design ·
§2 Operating Point · §3 Results · §4 Economics · §5 Export). Live everywhere, kein
„Calculate"-Button, Quelle hinter jedem Wert, Validation-Badge immer sichtbar.

## Nächst-Session-Briefing — ADR-009 Implementation (StackGeometry)

**Spec ist accepted** (siehe `docs/adr/009-stack-geometry-model.md`), Implementation steht aus. Empfohlenes Modell: **Sonnet + medium**, frischer Context.

**Scope (breaking — v0.2.0 Minor-Bump):**
- `schema/stack_geometry.py` (NEU) — `StackGeometry` + `DEFAULT_GEOMETRY`
- `schema/component.py` — `footprint`-Field entfernen (clean cut)
- `geometry/extruded.py` — Signatur auf `build_extruded(component, footprint)`
- `geometry/stack_assembly.py` — `geometry: StackGeometry` Kwarg, Overhang-Logik
- `ui/stack_geometry_panel.py` (NEU) — Active-Area-Picker + 6 Overhang-Spinner; emittiert `geometry_changed`
- `ui/main_window.py` — Panel verdrahten, STEP-Sidecar um `stack_geometry`-Block ergänzen
- `library/components/*.json` — `footprint`-Blöcke aus allen ~18 Einträgen entfernen
- Tests: `test_stack_geometry.py` (NEU), bestehende `test_geometry_extruded.py` + `test_geometry_stack_assembly.py` an neue Signatur anpassen
- Version-Bump 0.1.1 → 0.2.0 in `__init__.py` + `pyproject.toml` + CHANGELOG
- `assembly_to_sidecar` erweitern um Geometry-Block

**Quelle für Default Active-Area:** `@rost2022fuelcells` (5×5 cm Square, schon in `sources.bib`).

**Reihenfolge:** Schema → Library-Cleanup → Geometry/Assembly-Refactor → Tests grün → UI-Panel → STEP-Sidecar update → STATUS+CHANGELOG → v0.2.0-Tag.

---

## Letztes Briefing (erledigt) — ADR-008 Stack-Geometrie + STEP-Export

**Warum 008, nicht 007:** UX-VISION §16 reserviert ADR-007 „evtl." für
Compare-Drawer (v1.x). Bewusst frei lassen, um diese Reihenfolge nicht
zu verdrängen.

**Voraussetzung:** Branch `claude/beautiful-diffie-eb0ac2` ist in
v0.1.0 gemerged oder ausgecheckt. Auf dieser Branch existieren ADR-005
(LCOH) und ADR-006 (Stack-Composer) sowie die `StackBuild`-Dataclass.

**Pflichtlektüre vor ADR-Draft:**
- `docs/UX-VISION.md` §10 (Exports) + §13 (Roadmap-Mapping)
- `docs/adr/004-physics-model.md` (Format-Konvention)
- `docs/adr/006-stack-composer.md` (StackSelection-Datenklasse, die der STEP-Export konsumieren wird)
- `src/pem_ec_designer/assembly/stack.py` — `build_stack` liefert schon `StackBuild`
- `src/pem_ec_designer/geometry/extruded.py` — build123d-Pattern für **eine** Komponente
- `src/pem_ec_designer/ui/main_window.py:_on_export_csv` — Pattern für `_on_export_step`

**5 Design-Fragen, die ADR-008 entscheiden muss:**

1. **Footprint-Aggregation.** BPP (~80 mm) > GDL (~55 mm) > Membrane
   (50 mm aktiv). Optionen: (a) jede Schicht ihre eigene Größe,
   (b) gemeinsame Bounding-Box (alle = BPP-Footprint), (c) konzentrische
   Stufen wie in echten Zellen. **Welche?**
2. **Layer-Reihenfolge.** Fest `[BPP→GDL→CL→Membrane→CL→GDL→BPP]`
   hardcoded, oder StackSelection-Order konfigurierbar?
3. **Z-Achse.** Physikalisch korrekt (Membran 25 µm vs. BPP 5 mm =
   Faktor 200, im CAD-Viewer optisch unbrauchbar) oder Z-Exaggeration
   mit Faktor + Toggle? UI-Viewer macht aktuell ×100.
4. **Gasket-Layer.** Aktuell keine Gasket-Komponenten in Library —
   im STEP weglassen, Dummy einfügen, oder ADR sagt
   „Library-Erweiterung Voraussetzung"?
5. **Per-Komponente STEP-Color.** build123d/OCP unterstützt Farben
   in STEP eingeschränkt. Versuchen, oder bewusst monochrom + separate
   Material-Liste als Metadaten?

**Reihenfolge:** Erst ADR-008 in `docs/adr/008-stack-geometry-export.md`,
User-OK abwarten, dann Code: `geometry/stack_assembly.py` +
`_on_export_step` Handler in MainWindow + Tests + STATUS-Update +
README-Update.

**Modelle:** Opus + high effort für ADR-008-Draft, Sonnet + medium für
Implementation. Wenn Frage nicht aus Library/UX-VISION beantwortbar →
**fragen, nicht raten** (Strict-Quellen-Prinzip auch für Designentscheidungen).

---

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
