# Library — component specifications

This directory is the **single source of truth** for component data.
The Python package consumes it; the UI displays it; CAD generators
read parametric values from it.

## Layout (per ADR-002)

```
library/
├── schema.json         # auto-generated, do NOT edit (CI-checked)
├── materials.json      # ~20 materials, referenced by components
├── sources.bib         # BibTeX of all papers + datasheets
└── components/
    ├── membrane.json
    ├── anode_cl.json
    ├── cathode_cl.json
    ├── gdl.json
    ├── bpp.json
    ├── flow_field.json
    ├── endplate.json
    └── gasket.json
```

## How to add a component

1. Pick the right file under `components/{category}.json`.
2. Use a hierarchical ID: `{category}.{family}.{variant}`,
   e.g. `membrane.nafion.117`.
3. Reference the material via `{"ref": "<material-id>"}`. If the
   material does not exist yet, add it to `materials.json` first.
4. Every numerical value is a `SourcedValue`:
   ```json
   "thickness": {
     "value": { "value": 183, "unit": "um" },
     "source": "chemours.datasheet.n117"
   }
   ```
5. The `source` ID must resolve to a BibTeX key in `sources.bib`.
   If you don't have a real source, **leave the field out** (set to
   `null`). Do not invent a source. (Strict-Quellen, ADR-002 D4.)
6. Run `python -m pem_ec_designer.schema.cli` to regenerate `schema.json`.
7. Run `pytest tests/` to verify cross-validation.

## What lives here vs. in code

- **Here:** numeric data, material properties, geometry parameters
  (footprint, channel widths), prices, source citations.
- **In code (`src/pem_ec_designer/`):** physics formulas, geometry
  generators (build123d), UI rendering, validation logic.

The boundary is intentional: data changes go through Git diffs on
JSON, code changes go through Git diffs on Python. Two reviewable
streams.
