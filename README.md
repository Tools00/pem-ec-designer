# pem-ec-designer

Visual designer for **PEM water-electrolysis cells** — parametric
component library, CAD-quality 3D, polarisation physics.

**Status:** v0.0.1 (unreleased) — pre-alpha. Schema scaffolded, **18 components
across 5 categories** (membrane · GDL · anode CL · cathode CL · BPP) with
20 BibTeX sources. **UI v0 runs**: PySide6 MainWindow with library sidebar
+ embedded VTK viewer. Launch: `PYTHONPATH=src python -m pem_ec_designer`.
See [`CHANGELOG.md`](CHANGELOG.md) and [`docs/STATUS.md`](docs/STATUS.md).

## What this is

A desktop simulation tool that lets you:

- Pick electrolyzer components from a curated, source-cited library
- Compose them into a stack with parametric geometry
- Compute polarisation curves, efficiency waterfalls, and LCOH
- Export the geometry as STEP/STL via [build123d](https://build123d.readthedocs.io/)

Successor of [`../pem-ec-0d/`](../pem-ec-0d/), which is frozen at v0.6.

## Quickstart (development)

```bash
# 1. create venv
python3.11 -m venv .venv
source .venv/bin/activate

# 2. install package + dev deps (UI deps separate, optional)
pip install -e ".[dev]"

# 3. regenerate JSON schema from Pydantic models
python -m pem_ec_designer.schema.cli

# 4. run tests
pytest

# 5. (later, when UI lands) install UI deps
pip install -e ".[ui]"
```

## Architecture

See `docs/adr/` for the decision record:

| ADR | Topic |
|---|---|
| [001](docs/adr/001-framework-choice.md) | Framework: PySide6 + pyvistaqt + build123d |
| [002](docs/adr/002-library-architecture.md) | Library: Pydantic schema, BibTeX sources, hierarchical IDs |
| [003](docs/adr/003-qt-binding-license.md) | Qt binding: PySide6 (LGPL) — keeps product license free |

Layer structure (per ADR-001 §3.1):

```
src/pem_ec_designer/
├── ui/             # PyQt6 widgets         (framework-specific)
├── visualization/  # pyvistaqt + build123d (library-specific)
├── assembly/       # stack composition     (framework-agnostic)
├── physics/        # 0D physics, pure fns  (no Qt imports)
├── materials/      # library loader
├── schema/         # Pydantic models       (single source of truth)
└── foundation/     # constants, units      (CODATA 2018, SI internal)
```

## The library

`library/` is the data side — JSON specs + BibTeX sources, edited
by humans, validated by Pydantic. See [`library/README.md`](library/README.md)
for how to add a component.

Strict-quellen-policy (ADR-002 D4): every numerical value must cite
a paper or datasheet. Cross-validation runs on every load — missing
references break tests.

## Validation status

| Gate | Status |
|---|---|
| `import pem_ec_designer.physics` without Qt | ✓ tests/test_no_qt_imports.py |
| Unit round-trip for foundation.units | ✓ tests/test_units.py |
| Pydantic schema rejects flat IDs, accepts hierarchical (incl. underscore) | ✓ tests/test_schema.py |
| Library cross-validation (18 components, 5 categories) | ✓ tests/test_library.py |
| build123d STEP-export smoke (membrane, GDL, flow-field) | ✓ tests/test_geometry.py |
| PySide6 + pyvistaqt MainWindow renders headless to PNG | ✓ scripts/smoke_mainwindow.py |
| **Total** | **88/88 passing** |

## Roadmap

See [`docs/decisions/000-roadmap.html`](docs/decisions/000-roadmap.html).

## License

Code license TBD for the eventual product release. Qt binding is
**PySide6 (LGPL)** per [ADR-003](docs/adr/003-qt-binding-license.md),
which keeps the product license free (proprietary or GPL both possible).
PyQt6 (GPL) explicitly rejected.
