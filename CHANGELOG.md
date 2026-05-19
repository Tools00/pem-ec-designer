# Changelog

All notable changes to **pem-ec-designer** are tracked here.
Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [Unreleased]

(no changes since v0.1.1)

## [0.1.1] — 2026-05-19

### Added
- ADR-008: Stack-Geometrie-Aggregation + STEP-Export.
- `geometry/stack_assembly.py` — pure (no-Qt) Aggregation der 7 PEM-Layer in
  fixer Reihenfolge `[BPP→GDL→CL→Membrane→CL→GDL→BPP]`, true SI Z-Achse,
  per-Layer Footprint aus Library.
- UI: `STEP…`-Button in §5 Export schreibt `<name>.step` plus Sidecar
  `<name>.layers.json` mit Material/Role-Mapping (ADR-008 §D5).
- 5 Tests in `tests/test_geometry_stack_assembly.py` (Layer-Order, Skipped-
  Layer, fehlender Footprint, STEP-Roundtrip, Sidecar-Shape).

### Fixed
- Version-Drift: `__version__` und `pyproject.toml` waren bei v0.1.0-Release
  noch `0.0.1`. Auf `0.1.1` gebumpt — STEP-Sidecar zitiert nun korrekt.

## [0.1.0] — 2026-05-19

> **First end-to-end usable cut.** Single-page UI with composer +
> operating sliders + V–I plot + loss waterfall + LCOH readout +
> CSV/BibTeX export — all live and source-cited. 226/226 tests, ADRs
> 001–006 accepted. MIT-licensed.

**Highlights vs. v0.0.1:**

- `physics/efficiency.py` + `physics/lcoh.py` — η_LHV + Schmidt-2017 LCOH
- `assembly/library_filter.py` + `assembly/source_collector.py` —
  category filters + cited-source extraction
- `ui/stack_composer.py` — 9 dropdowns replacing the v0 hardcoded stack
- Single-page `QScrollArea` UI with 5 numbered sections (no more tabs)
- `ui/source_tooltip.py` + `ui/validation_badge.py` — Bernt-2016 anchor
- `ui/economics_panel.py` — LCOH live readout, slider-driven
- Design-j slider with marker sync on V–I + waterfall
- `export/csv_export.py` + `export/bibtex_export.py` — first real exports
- `ui/persistence.py` — QSettings auto-save for stack/op/lcoh/window/ui
- `ui/onboarding_banner.py` + keyboard shortcuts (Cmd+E/D/R, ?)

**Tests:** 88 → **226** across this release window.

---

### Added (UX polish part 2b — persistence + shortcuts + onboarding · May 2026) ★
- `ui/persistence.py` — typed save_*/restore_* helpers around `QSettings`
  for `stack/*`, `op/*`, `lcoh/*`, `window/*`, `ui/*` keys per UX-VISION §9.
- StackComposer, OperatingPanel, EconomicsPanel gain `set_state(…)` with
  `blockSignals` so restoring doesn't cascade into a recompute.
- MainWindow restores stack + operating point + LCOH at `__init__`,
  persists on every meaningful change (composer, sliders, resize).
- `__main__` sets `QCoreApplication.setOrganizationName/Application`
  before constructing `QApplication` so QSettings is consistent cross-platform.
- Keyboard shortcuts (UX-VISION §11 v1.0 subset): `Cmd+E` export CSV,
  `Cmd+D` toggle 3D preview, `Cmd+R` reset to defaults, `?` help dialog.
- `ui/onboarding_banner.py` — single dismissible hint above the
  scroll area; auto-dismisses on first slider/dropdown change; flag
  persisted as `ui.onboardingSeen` (UX-VISION §8).
- Tests: +11 persistence Ini-roundtrip (tmp_path-isolated), +3
  onboarding-banner. Total **226/226**.

### Added (UX polish part 2a — design-j + exports · May 2026) ★
- **Design-j slider** in §2 (0.1–4.0 A/cm²) with separate `design_j_changed`
  signal. Moving it does NOT rebuild the stack — only repositions the marker
  on the V–I plot + waterfall, updates the LCOH read-out, and re-evaluates
  the Validation-Badge. UX-VISION §6.2 "besondere Rolle" honoured.
- PolarisationPanel: dashed vertical line + bold red dot at design_j on both
  subplots. Annotation `design  V = X.XXX V @ Y.Y A/cm²`. V(1)/V(2) markers
  demoted to small grey dots (literature anchors).
- `assembly/source_collector.py` — `collect_source_keys()` walks
  Component/Material `SourcedValue` fields and returns the set of unique
  BibTeX keys with locator suffixes (`.tab2`, `.fig1a`, `.eq3`) stripped.
  Datasheet keys (`chemours.datasheet.n117`) preserved.
- `export/csv_export.py` — V–I CSV with self-documenting comment header
  (T/p, stack components, sources cited, design-j). UX-VISION §10 format.
- `export/bibtex_export.py` — subset of `library/sources.bib` containing
  only the keys cited by the current stack. Minimal brace-balanced
  parser; missing keys reported via return value.
- MainWindow §5 Export: `V–I CSV…` + `Citations .bib…` buttons replace
  the v0 placeholder, wired through `QFileDialog`.
- Tests: +9 source-collector (bibtex-key stripping, datasheet-id
  preservation), +13 csv + bibtex-export. Total **212/212**.

### Added (UX polish part 1 · May 2026) ★
- **Single-page scroll layout** — `QTabWidget` is gone. MainWindow now
  has a header (title + Validation-Badge) and a `QScrollArea` with five
  labelled sections per UX-VISION §4: §1 Stack Design (Composer +
  collapsible 3D viewer, default closed) · §2 Operating Point · §3
  Results · §4 Economics · §5 Export (placeholder).
- `ui/source_tooltip.py` — pure HTML-tooltip formatter for
  `SourcedValue` (and convenience wrappers for thickness / catalyst
  kinetics). No Qt imports — testable as a string function.
- `ui/validation_badge.py` — header badge ✓/⚠/✗ comparing model
  V(1 A/cm²) to the Bernt-2016 anchor (1.60 V midpoint). Click opens a
  QMessageBox with the anchor band, deviation %, and BibTeX key.
  Thresholds 5 % / 15 % per UX-VISION §6.4.
- StackComposer dropdowns + 3D-viewer list now carry per-item tooltips
  pulled from `format_thickness_tooltip` — hover shows BibTeX source.
- Tests: +8 source-tooltip, +11 validation-badge (classification logic).
  Total **190/190**.

### Added (stack composer · May 2026) ★
- **ADR-006** — Stack-Composer architecture: 9 Library-Filter-Dropdowns,
  σ-cut-off 100 S/m for membrane materials (separates ionomers from
  graphitic BPP substrates without a schema `category` field), rejected
  alternatives (Drag-&-Drop, JSON-Editor, Tree-Selector) documented.
- `assembly/library_filter.py` — 8 pure functions
  (`membranes`, `anode_catalyst_layers`, …, `cathode_catalyst_materials`),
  no Qt dependency, deterministic sort.
- `ui/stack_composer.py` — `QGroupBox` mit 9 `QComboBox`-Dropdowns,
  emittiert `selection_changed` für Live-Replot. Defaults reproduzieren
  den v0-Hardcoded-Stack (P7 „Default ist sinnvoll").
- `main_window`: `_build_default_stack` → `_build_stack_from_composer`,
  liest `composer.current_selection()` und ruft das unveränderte
  `assembly.stack.build_stack()`.
- Tests: +9 library-filter (Sortierung, σ-Cut-off, Disjunktheit,
  Determinismus, no-Qt-import). Total **171/171**.

### Added (economics layer · May 2026) ★
- **ADR-005** — LCOH model: amortised CapEx + fixed OpEx + grid electricity,
  Schmidt-2017 style. Rejected alternatives (stack replacement, system-wide
  boundary, Monte-Carlo, faradaic-η < 1) documented with reasons.
- `physics/efficiency.py` — `lhv_efficiency(V_cell)`, `hhv_efficiency(V_cell)`,
  `specific_energy_consumption(V_cell)`. V_LHV_thermoneutral = 1.253 V
  derived from CODATA LHV_H2.
- `physics/lcoh.py` — `LCOHInputs` dataclass with Schmidt-2017 defaults,
  `capital_recovery_factor()`, `levelised_cost_of_hydrogen()` returning
  per-component breakdown (CapEx / OpEx / Strom).
- Validation anchor met: 3.71 €/kg @ η_LHV = 0.65, 50 €/MWh, 1100 €/kW,
  CF 90 %, 25 y, i = 8 % — inside Schmidt-2017 PEM band (3.5–5.5 €/kg
  at 50 €/MWh).
- `ui/economics_panel.py` — §4 LCOH live read-out with CapEx + Strompreis
  sliders, wired into MainWindow `_recompute_polarisation`. V_cell @ 1 A/cm²
  (design-j anchor) feeds the panel; recomputes < 1 ms per slider change.
- Tests: +37 (9 efficiency, 28 lcoh inkl. Schmidt-Anker, CRF edge cases,
  monotonicity). Total **162/162**.

### Added (physics layer · May 2026) ★
- **ADR-004** — physics-model choice: 0D · steady-state · isothermal ·
  symmetric Butler-Volmer + linear ASR-sum. Five axes traded off with
  rejected alternatives documented; calibration factors explicitly
  forbidden.
- `physics/thermodynamics.py` — `reversible_voltage(T, p_h2, p_o2)`
  with Nernst correction and tabulated dE/dT = −8.46×10⁻⁴ V/K.
  Validated: 1.229 V @ 25 °C (CODATA), 1.183 V @ 80 °C (Newman 2021).
- `physics/kinetics.py` — `butler_volmer_overpotential` (symmetric)
  + `tafel_slope`. Bernt 2016 (47 mV/dec) cross-check.
- `physics/ohmic.py` — `OhmicContribution` dataclass +
  `total_asr` / `ohmic_overpotential` (series sum) +
  `asr_from_thickness_and_conductivity` (membrane helper).
- `physics/polarization.py` — **master function `cell_voltage(j, …)`
  + sweep `polarisation_curve(j_values, …)`** composing all of the
  above. Returns `PolarisationPoint` with each loss term broken out
  for waterfall display.
- Validation anchors per ADR-004 met: V(1 A/cm², 80 °C) = 1.632 V
  ∈ Bernt-2016 band [1.50, 1.70]; V(2 A/cm², 80 °C) = 1.764 V
  ∈ Carmo-2013 band [1.70, 2.00].
- Tests: +33 (6 thermodynamics, 12 kinetics, 8 ohmic, 7 polarization).
  Total 121/121.

### Added (library expansion · May 2026)
- **GDL** family completed: Toray TGP-H -030 / -060 / -090 / -120 +
  SIGRACET 22 BB / 28 BC / 36 BB / 39 BB — all from manufacturer
  datasheets (8 specs total).
- **Anode CL** category: 2 specs from Bernt & Gasteiger 2016 JES
  (IrO₂/TiO₂, 2.0 + 1.46 mg_Ir/cm², ionomer-content series).
- **Cathode CL** category: 2 specs from Zhang et al. 2024
  ACS Appl. Mater. Interfaces (Pt/HSAC, baseline 0.1 + ultralow
  0.025 mg_Pt/cm²).
- **BPP** category: research-cell POCO AXF-5Q (5 mm) +
  `poco-axf5q` material spec.
- BibTeX +4: `bernt2016jes` (key fixed from `bernt2018jes` — vol. 163
  of JES is 2016, not 2018), `zhang2024acsami`,
  `entegris.datasheet.axf5q`, `chen2022jpowsour`.
- Units: `mg/cm^2` (catalyst loading) registered with round-trip +
  equivalence tests.
- Schema: hierarchical-ID pattern loosened to allow underscore in
  segments so `anode_cl.*` / `cathode_cl.*` / `flow_field.*` IDs validate.

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
