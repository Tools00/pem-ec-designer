# Changelog

All notable changes to **pem-ec-designer** are tracked here.
Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [SemVer](https://semver.org/).

## [Unreleased]

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
