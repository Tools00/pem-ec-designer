# Changelog

All notable changes to **pem-ec-designer** are tracked here.
Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- `geometry/` layer (headless build123d CAD, no Qt).
- `build_extruded(component) → Part` — generic extruder for any
  `Component` with `footprint` + `thickness`. Handles circular, square,
  rectangular footprints; SI→mm at the boundary.
- `build_membrane(spec)` — thin type-narrowing wrapper.
- `Footprint` re-exported from `pem_ec_designer.schema`.
- Tests:
  - real Nafion 117 → volume + STEP smoke (ISO-10303 magic header);
  - synthetic GDL → rectangular + square branches, missing-footprint
    and missing-diameter error paths;
  - real Membrane round-trip via generic builder.
- `geometry/` covered by no-Qt layer-separation test.

### Changed
- `geometry.membrane.build_membrane` now delegates to `build_extruded`
  (logic moved to `geometry/extruded.py`). API unchanged.

### Added (UI v0)
- `python -m pem_ec_designer` opens a MainWindow with library sidebar
  + embedded VTK viewer. Selecting a component renders it via
  `build_extruded` -> STL -> pyvista. ADR-001 launch gate satisfied.
- `ui/qt_env.py` — sets QT_PLUGIN_PATH for anaconda Python (must be
  imported before any PySide6 import).
- `ui/main_window.py` — sidebar + QtInteractor + status bar with
  source citation.
- `ui/viewer.py` — build123d Part -> pyvista mesh bridge.
- `scripts/smoke_mainwindow.py` — headless launch + screenshot
  verification (re-runnable after every UI change).

### Validated
- UI render stack on macOS arm64: PySide6 + pyvistaqt + VTK pipeline
  proven end-to-end via `scripts/smoke_pyvistaqt.py` (membrane STL →
  embedded VTK render → PNG screenshot, 8 KB). 3 platform-specific
  pitfalls documented in `docs/UI-LAUNCH-NOTES.md` (QT_PLUGIN_PATH,
  no offscreen on macOS arm64, render-before-screenshot order).

### Decided
- ADR-003: Qt-Binding = **PySide6 (LGPL)**. Formalisiert die im
  pyproject schon implizit getroffene Wahl. Hält Produkt-Lizenz frei
  (proprietär oder GPL möglich). PyQt6 explizit verworfen.

### Added (flow-field)
- `build_flow_field(spec)` — first non-pure-extrusion generator.
  Subtracts a parallel channel pattern from a base plate.
  Pattern `straight_parallel` implemented; serpentine / interdigitated
  / mesh / pin_fin raise `NotImplementedError`.
- Validation: rejects circular footprint, channel overlap
  (pitch < width), channels deeper than plate.
- 6 tests (volume = plate − n·channel exact; STEP smoke; 4 error paths).
- `geometry.flow_field` covered by no-Qt layer-separation test.

## [0.0.1] — 2026-04-27

### Added
- ADR-001: framework choice — PyQt6 + pyvistaqt + build123d.
- ADR-002: library architecture — Pydantic v2, per-category JSON,
  hierarchical IDs, explicit unit objects, BibTeX sources.
- Foundation layer (`constants.py` CODATA 2018, `units.py` SI ↔ engineering).
- Schema layer (`Quantity`, `SourcedValue`, `Material`, `Component` + 8 subclasses).
- Library loader with cross-validation (material refs, source IDs).
- Library skeleton:
  - 2 materials (Nafion-1100 PFSA, Aquivion-870 SSC).
  - 5 membrane specs (Nafion 115, 117, 211, 212, Aquivion E87-05S).
  - BibTeX with 11 entries (papers + datasheets).
- Tests: unit round-trip, schema validation, library cross-validation,
  no-Qt smoke test.
- Decision pages (interactive HTML) under `docs/decisions/`.

### Notes
- No UI yet. PyQt code lands in v0.1.
- Costs are deliberately omitted in v0.0.1 — strict-quellen requires
  real source for prices, internal estimates flagged TODO.
