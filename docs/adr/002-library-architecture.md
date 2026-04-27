# ADR-002 — Library-Architektur

**Status:** Accepted
**Datum:** 2026-04-27
**Vorgänger:** ADR-001 (Framework-Wahl: PyQt + pyvistaqt + build123d)
**Nachfolger:** ADR-004 (Geometry-Generator-Binding), ADR-005 (Stack-Composition)
**Late binding:** ADR-003 (Lizenz-System)

---

## Context

ADR-001 hat den Tech-Stack festgelegt. Damit ist Python-Scaffold erlaubt,
aber bevor Code entsteht, muss die Library-Architektur stehen — sonst
wachsen Schema und Code unabhängig auseinander.

Vorgaben aus Library-Scope (`docs/decisions/001-library-scope.html`):

- **Form C:** Python-Package mit build123d
- **Quellen Strict:** jede Zahl mit Paper/Datasheet-Referenz
- **Sprache Hybrid:** EN-Specs, DE-UI
- **Umfang Wide:** ~60+ Komponenten

---

## Decision

Sechs Architektur-Punkte, alle nach Default-Empfehlung aus
`docs/decisions/004-library-architecture.html`:

| # | Punkt | Wahl | Kurz-Begründung |
|---|---|---|---|
| D1 | Storage-Layout | **Per Category** — `library/components/{cat}.json` | Diff-friendly, ~8 Files mit ~7 Items, gut review-bar |
| D2 | Spec-Validierung | **Pydantic v2 + auto-gen JSON Schema** | Runtime + Editor-Validation, Single Source of Truth |
| D3 | Material vs Component | **Material separat, per Reference** | DRY — „Nafion 117" einmal definiert, N-fach referenziert |
| D4 | Quellen-Storage | **Ref-ID + BibTeX** | Standard für wissenschaftliche Reproduzierbarkeit |
| D5 | Component-IDs | **Hierarchical** — `membrane.nafion.117` | Sortierbar, machine-parseable, human-readable |
| D6 | Engineering-Units | **Explicit object** — `{value, unit}` | Verwechslungs-frei, alle Paper-Units (µm/mil/m) direkt übernehmbar |

---

## Resulting structure

```
pem-ec-designer/
├── library/                       # alles human-editable JSON/YAML
│   ├── schema.json                # auto-gen aus Pydantic, für VS Code
│   ├── materials.json             # ~20 Materialien, single source
│   ├── sources.bib                # BibTeX aller Paper + Datasheets
│   ├── components/
│   │   ├── membrane.json          # Nafion 115/117/212, Aquivion, ...
│   │   ├── anode_cl.json          # IrO2, IrRuO2, IrO2/TiO2
│   │   ├── cathode_cl.json        # Pt/C variants
│   │   ├── gdl.json               # Ti-Felt, Ti-sinter, carbon paper
│   │   ├── bpp.json               # Ti, coated Ti, SS316
│   │   ├── flow_field.json        # straight/serpentine/interdigit/mesh
│   │   ├── endplate.json          # SS, Al
│   │   └── gasket.json            # EPDM, PTFE, Viton
│   └── README.md                  # how to add a component
└── src/pem_ec_designer/
    ├── schema/                    # Pydantic-Modelle (Single Source)
    │   ├── component.py           # Component-Basisklasse + Subklassen pro Kategorie
    │   ├── material.py            # Material + MaterialRef
    │   ├── source.py              # SourcedValue, BibTeX-Loader
    │   └── units.py               # Quantity {value, unit} → SI-Konversion
    ├── materials/                 # Loader-Logik (liest JSON via Pydantic)
    │   └── loader.py
    └── ... (übrige Layer aus ADR-001)
```

---

## Schema-Beispiele (canonical)

### Material (in `library/materials.json`)

```json
{
  "nafion-117": {
    "name": "Nafion 117",
    "vendor": "Chemours",
    "family": "PFSA membrane",
    "sigma_S_per_m": {
      "value": { "value": 10, "unit": "S/m" },
      "source": "kusoglu2017chemrev.tab1"
    },
    "ewt_g_per_eq": {
      "value": { "value": 1100, "unit": "g/eq" },
      "source": "chemours.datasheet.n117"
    }
  }
}
```

### Component (in `library/components/membrane.json`)

```json
{
  "membrane.nafion.117": {
    "category": "membrane",
    "name": "Nafion 117 · 183 µm",
    "material": { "ref": "nafion-117" },
    "thickness": {
      "value": { "value": 183, "unit": "um" },
      "source": "chemours.datasheet.n117"
    },
    "cost_eur": {
      "value": { "value": 120, "unit": "EUR/cell" },
      "source": "chemours.pricelist.2024"
    },
    "form": {
      "footprint": "circular",
      "diameter": { "value": 50, "unit": "mm" }
    }
  }
}
```

### BibTeX-Eintrag (in `library/sources.bib`)

```bibtex
@article{carmo2013ijhe,
  author  = {Marcelo Carmo and David L. Fritz and Jürgen Mergel and Detlef Stolten},
  title   = {A comprehensive review on PEM water electrolysis},
  journal = {International Journal of Hydrogen Energy},
  volume  = {38}, number = {12}, pages = {4901--4934}, year = {2013},
  doi     = {10.1016/j.ijhydene.2013.01.151}
}

@misc{chemours.datasheet.n117,
  author = {Chemours},
  title  = {Nafion N115, N117, N1110 Membranes — Product Information},
  year   = {2024},
  note   = {accessed 2026-04-27}
}
```

### Pydantic-Modell (in `src/pem_ec_designer/schema/component.py`)

```python
from pydantic import BaseModel
from .units import Quantity
from .source import SourcedValue
from .material import MaterialRef

class Component(BaseModel):
    id: str                       # "membrane.nafion.117"
    category: str
    name: str
    material: MaterialRef
    thickness: SourcedValue[Quantity]
    cost_eur: SourcedValue[Quantity]
    form: dict                    # extended in subclasses
```

---

## Consequences

### Positiv

- **Schema-Single-Source:** `model_json_schema()` erzeugt `library/schema.json`
  → VS Code validiert beim Tippen, keine Doppel-Pflege.
- **Material-Update an einer Stelle:** `nafion-117`-Werte ändern wirkt
  automatisch in allen Komponenten, die darauf zeigen.
- **Strict-Quellen-Pflicht erzwingbar:** Pydantic-Validator kann
  `SourcedValue.source` als Required markieren — ohne Source kein Load.
- **Unit-Konflikte unmöglich:** Pydantic-Validator konvertiert beim
  Laden zu SI; alle internen Funktionen rechnen ausschließlich SI.
- **BibTeX-Kompatibilität:** Pandoc, Zotero, JabRef können
  `sources.bib` direkt konsumieren.

### Negativ

- **Mehr Boilerplate** als „dict-of-dicts": jedes Spec-Feld ist
  ein `SourcedValue[Quantity]` statt einer Zahl. Lesbarkeit der JSON
  leidet.
- **Materials werden zentralisiert**, was beim Lesen einer Component
  einen extra Resolve-Schritt bedeutet (Vorteil: DRY; Nachteil:
  Component nicht mehr 100 % self-contained beim Diffen).
- **Auto-gen Schema** muss in CI gegen committed `schema.json`
  geprüft werden, sonst driftet's.

### Neutral

- ADR-004 (Geometry-Generator-Binding) bleibt offen. Generatoren
  liegen vorerst als `Component.build()`-Stubs, Refactor entscheidet
  sich nach 5 prototypischen Generatoren.

---

## Validation des ADRs

Smoke-Tests, die spätestens v0.1 grün sein müssen:

- [ ] `pydantic.BaseModel.model_json_schema()` erzeugt `schema.json`
  identisch zu committed Version (CI-Check)
- [ ] Component mit fehlendem `source`-Feld wird beim Load abgewiesen
- [ ] `MaterialRef("nafion-117")` resolved gegen `materials.json`
- [ ] `Quantity(183, "um")` und `Quantity(0.183, "mm")` ergeben
  identischen SI-Wert (`1.83e-4 m`)
- [ ] Reference-ID in Component (z.B. `carmo2013ijhe.tab2`) findet
  passenden BibTeX-Entry in `sources.bib`

---

## References

- `docs/adr/001-framework-choice.md`
- `docs/decisions/001-library-scope.html`
- `docs/decisions/004-library-architecture.html`
- `Simulation-tools/docs/simulation-project-framework.md` §3.1, §3.3, §3.4
- Pydantic v2: <https://docs.pydantic.dev/latest/>
- BibTeX: <https://www.bibtex.org/Format/>
