# ADR-008 — Stack-Geometrie-Aggregation und STEP-Export

**Status:** Accepted
**Datum:** 2026-05-19
**Vorgänger:** ADR-001 (Framework), ADR-002 (Library), ADR-004 (Physics-Model), ADR-006 (Stack-Composer)
**Nachfolger:** —

> Warum 008, nicht 007: UX-VISION §16 reserviert ADR-007 „evtl." für Compare-Drawer (v1.x).
> Bewusst freilassen, um diese Reihenfolge nicht zu verdrängen.

---

## Context

UX-VISION §10 listet `.step` als **v1.0-Pflicht-Export**: „3D-Geometrie des
gesamten Stacks (alle gewählten Komponenten gestapelt) · selbstdokumentierend".

Heute existiert:
- `geometry/extruded.py:build_extruded(component)` — extrudiert **eine** Komponente
  aus ihrem `footprint` + `thickness`. STEP-Export für einzelne Parts verifiziert.
- `assembly/stack.py:build_stack(...)` — liefert `StackBuild` (Physik-Inputs).
  Trägt **keine** Geometrie-Aggregation.
- `ui/main_window.py` — hat `_on_export_csv` und `_on_export_bibtex`, **keinen**
  `_on_export_step`-Handler.

Lücke: es gibt keinen Mechanismus, der die per Stack-Composer ausgewählten
7 Layer zu einem `build123d.Compound` stapelt und als STEP-Datei
schreibt.

5 Designfragen waren offen; alle in Session 2026-05-19 mit User entschieden
(siehe Decision).

---

## Decision

Eine neue, **reine** (Qt-freie) Funktion
`geometry/stack_assembly.py:build_stack_assembly(selection) -> StackAssembly`
aggregiert die `StackSelection` (aus ADR-006) zu einem `build123d.Compound`
plus Material-Mapping. Die UI bekommt einen `_on_export_step`-Handler nach
dem Muster von `_on_export_csv`.

### D1 · Footprint-Aggregation: per-Layer aus Library

Jeder Layer extrudiert seinen **eigenen** `Component.footprint`. Wenn die
Library später (Pfad A) realistische Maße für BPP (~80 mm) und GDL (~55 mm)
einträgt, wird der STEP automatisch gestuft, **ohne Code-Änderung** in
`stack_assembly`.

v1.0-Konsequenz: alle Library-Components haben aktuell ∅50 mm zirkulär,
der STEP ist also ein gleichmäßiger Zylinderstapel. Das ist ehrlich
(spiegelt die Library) und nicht erfunden.

Wenn ein Layer **kein** `footprint` hat (Library erlaubt `null`), wird er
mit Hinweis übersprungen — analog zum bestehenden `skipped_layers`-Muster
aus `StackBuild`.

### D2 · Layer-Reihenfolge: hardcoded fix

```
[anode_bpp] → [anode_gdl] → [anode_cl] → [membrane] → [cathode_cl] → [cathode_gdl] → [cathode_bpp]
```

Begründung wörtlich aus ADR-006: *„Geometrie der PEM-Zelle ist fix
(Anode → MEA → Cathode), nicht permutierbar. Reihenfolge ist keine
Designentscheidung."*

Nicht-vorhandene Layer (Composer hat `None` selektiert oder Library kein
Eintrag) werden ausgelassen, die übrigen rücken zusammen. Z-Position
wird kumulativ über die existierenden Thicknesses berechnet.

### D3 · Z-Achse: physikalisch korrekt im STEP, UI-Toggle separat

STEP-Datei enthält **wahre** SI-Dicken (Membran 25 µm = 0.025 mm, BPP
5 mm = 5 mm). Wer den STEP in SolidWorks/FreeCAD/COMSOL importiert, sieht
echte Maße — das ist der einzige zitierfähige Export.

Die Viewer-Exaggeration (aktuell ×100 im VTK-Panel) ist UI-Concern, kein
Export-Concern. Sie bleibt im 3D-Panel als optionaler Toggle (out of
scope für ADR-008 — separater UI-Polish-Schritt).

### D4 · Gaskets: weglassen, im STEP-Header dokumentieren

Library enthält **keine** Gasket-Komponenten. Dummy-Einfügen verstößt
gegen Strict-Quellen (ADR-002). Folgerung:

- v1.0: Gaskets fehlen im STEP. Sidecar-JSON-Metadaten (siehe D5)
  vermerken explizit `"gaskets": null` mit Erklärung.
- v1.x-Voraussetzung: Library bekommt `gasket`-Kategorie. Dann
  reicht ein Library-Eintrag — `stack_assembly` muss nicht geändert werden,
  da die Layer-Liste schon optional ist.

### D5 · STEP-Color: monochrom + Sidecar-JSON

build123d/OCP-Farbsupport ist STEP-Variant-abhängig und CAD-Tool-
abhängig — Versprechen, die wir nicht halten können. Stattdessen:

- STEP-Datei: monochrom (build123d default), nur Geometrie + STEP-
  Headerkommentar mit Stack-Beschreibung.
- **Sidecar `<name>.layers.json`** neben der STEP-Datei. Format:

  ```json
  {
    "stack": "PEM-EC single cell (pem-ec-designer v0.1.0)",
    "operating_point": {"T_K": 353.15, "p_h2_Pa": 1e5, "p_o2_Pa": 1e5},
    "layers": [
      {"index": 0, "role": "anode_bpp", "id": "bpp.poco.axf5q",
       "material": "poco-axf-5q-graphite", "thickness_m": 0.005,
       "footprint_mm": {"shape": "circular", "diameter": 50.0},
       "z_start_mm": 0.0, "z_end_mm": 5.0,
       "source_keys": ["poco_axf5q_datasheet"]},
      …
    ],
    "skipped": ["gasket — not in library v0.1.0"]
  }
  ```

  Die JSON ist die **Quelle der Wahrheit** für Layer-Identität und
  Material-Zuordnung. STEP allein bleibt geometrisch.

---

## Architecture

```
src/pem_ec_designer/
├── assembly/
│   └── stack.py                    ← unverändert (StackBuild)
├── geometry/
│   ├── extruded.py                 ← unverändert (build_extruded)
│   └── stack_assembly.py           ← NEU
└── ui/
    └── main_window.py              ← +_on_export_step

tests/
└── test_stack_assembly.py          ← NEU
```

### `geometry/stack_assembly.py` (Signatur-Skizze)

```python
@dataclass
class LayerPlacement:
    role: str                # "anode_bpp" | "anode_gdl" | … | "cathode_bpp"
    component_id: str
    part: build123d.Part     # bereits z-translatiert
    thickness_mm: float
    z_start_mm: float
    z_end_mm: float
    material_id: str | None

@dataclass
class StackAssembly:
    compound: build123d.Compound       # für STEP/STL-Export
    layers: list[LayerPlacement]       # für JSON-Sidecar
    skipped: list[str]                 # human-readable Gründe

LAYER_ORDER: tuple[str, ...] = (
    "anode_bpp", "anode_gdl", "anode_cl",
    "membrane",
    "cathode_cl", "cathode_gdl", "cathode_bpp",
)

def build_stack_assembly(selection: StackSelection) -> StackAssembly: ...
```

### `_on_export_step` (Muster wie `_on_export_csv`)

1. `QFileDialog.getSaveFileName(..., "STEP file (*.step *.stp)")`
2. `assembly = build_stack_assembly(self._composer.current_selection())`
3. `build123d.export_step(assembly.compound, path)`
4. JSON-Sidecar schreiben (`Path(path).with_suffix(".layers.json")`)
5. Statusbar: `STEP exported → {path} (+ sidecar)`

Edge-Cases: leerer Stack → MessageBox „No components selected"; build123d-
Fehler → MessageBox mit Fehlertext.

---

## Rejected Alternatives

| # | Alternative | Verworfen weil |
|---|---|---|
| A1 | Footprint-Bounding-Box über alle Layer (alle = max) | Versteckt zukünftige Library-Realität. Bei aktuell allen ∅50 mm wäre Ergebnis identisch — aber „funktioniert zufällig" ist kein Designprinzip. |
| A2 | Hardcoded BPP=80/GDL=55/Membrane=50 als Konstanten in `stack_assembly` | Werte ohne Library-Quelle = Strict-Quellen-Verstoß. |
| A3 | Layer-Reihenfolge in `StackSelection` per Index permutierbar | UX-VISION §1 + ADR-006: Stack-Geometrie ist physikalisch fix. Konfigurierbarkeit = Komplexität ohne Nutzen. |
| A4 | Z-Exaggeration in STEP einbacken | Macht den STEP CAD-untauglich. Niemand importiert einen ×100-Stack in SolidWorks für echte Konstruktion. |
| A5 | Gasket-Dummies mit Standard-Maß einfügen | Werte-Erfindung, Strict-Quellen-Verstoß. |
| A6 | Farben via build123d AP214-Color einbauen | Best-effort, brüchig über CAD-Tools, kein verlässliches Versprechen → wäre Anti-P3 („Quelle hinter jedem Wert"). |
| A7 | STEP-Sidecar als XML im STEP-Header statt JSON | STEP-Header-Comments sind nicht standardisiert lesbar von Tools. JSON neben STEP ist Toolchain-agnostisch und in Python trivial zu lesen. |

---

## Consequences

### Positiv
- STEP-Export erfüllt v1.0-Pflicht aus UX-VISION §10.
- Strict-Quellen bleibt durchgehend: keine erfundenen Maße, keine
  Geistgaskets, keine Farb-Versprechen.
- `stack_assembly.py` ist pure (kein Qt) → unit-testbar ohne UI-Mock.
- Sidecar-JSON ist von Anfang an versionsfähig (`stack`-Feld trägt App-
  Version) und passt zum späteren `.pemcell`-Format (UX-VISION §13.1).
- Backend-Funktion ist auch ohne UI nutzbar — Skript-Pipeline möglich.

### Negativ / akzeptierte Trade-offs
- STEP sieht im v1.0-Stand „langweilig" aus (gleichmäßiger ∅50-mm-Zylinder).
  Akzeptiert; spiegelt Library ehrlich. Fix kommt automatisch mit Pfad A.
- CAD-Tools, die STEP-Farben unterstützen, zeigen einen einfarbigen Stack.
  Sidecar-JSON macht das wett für Power-User; GUI-User sieht „nur Geometrie".
- Gaskets fehlen ganz. In der Statusbar (UX-VISION §6.5) wird das via
  `assembly.skipped` sichtbar.

---

## Test-Plan (für die anschließende Code-Session)

1. **Unit:** `build_stack_assembly` mit Default-Stack → 7 `LayerPlacement`,
   z_end == sum(thicknesses), keine skipped.
2. **Unit:** Stack ohne Anode-BPP → 6 Layer, `skipped` enthält Hinweis.
3. **Unit:** Layer mit `footprint=None` → in `skipped`, nicht im Compound.
4. **Integration:** Roundtrip STEP-Export + Re-Import (`build123d.import_step`)
   → gleicher Bounding-Box.
5. **Integration:** JSON-Sidecar lädt mit `json.load`, Schema-Check
   (alle 7 Roles vorhanden, `z_end` monoton).
6. **UI-Smoke:** `_on_export_step` in einem `qtbot`-Test (oder `pytest-qt`)
   → produziert Files an temp path ohne Exception.

---

## Referenzen

- UX-VISION §10 (Export-Formate) — STEP als v1.0-Pflicht.
- UX-VISION §13 (Roadmap-Mapping) — §5 EXPORT, „STEP-Export-Button" → Pfad C+.
- ADR-002 — Library-JSON-Strict-Quellen.
- ADR-004 — Physik-Model, Layer-Trennung.
- ADR-006 — `StackSelection`/`current_selection()` als Input.
- `docs/STATUS.md` § „Nächst-Session-Briefing — ADR-008".
