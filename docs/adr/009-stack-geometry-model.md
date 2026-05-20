# ADR-009 — Stack-Geometrie als globales Modell (StackGeometry)

**Status:** Accepted
**Datum:** 2026-05-20
**Vorgänger:** ADR-002 (Library), ADR-006 (Stack-Composer), ADR-008 (STEP-Export)
**Nachfolger:** —

---

## Context

Heutiges Schema: jeder `Component` trägt ein eigenes `footprint`-Feld
(`schema/component.py:79`). Alle Library-Einträge (Membrane, GDL, CL, BPP)
führen `footprint: { shape: circular, diameter: 50 mm }` als Pflichtdatum.

Das spiegelt nicht die Realität: eine SGL-39BB-GDL-**Rolle** ist 300 mm
breit (Datasheet); ihre Größe **in der Zelle** ist eine Funktion der
Test-Cell-Konvention, nicht der Komponente. Dasselbe gilt für Membranen
(Nafion kommt als Bahn), CLs (Coating-Fläche) und BPPs (Platten-Rohling).

ADR-008 nutzt diese Footprints für STEP-Export — aktuell mit dem
Ergebnis, dass alle 7 Layer ∅50 mm haben und der STEP ein gleichmäßiger
Zylinder ist. Strict-Quellen-konform, aber inhaltlich falsch:
**Footprint ist Stack-Property, nicht Component-Property.**

Session 2026-05-20 hat (a) globalen Stack-Footprint, (b) per-Layer-
Overhang im UI konfigurierbar, (c) clean cut der Migration bestätigt.
Quelle für Default 5×5 cm = 25 cm² Square: Rost et al. 2022.

---

## Decision

**Footprint wandert vom `Component` zu einem neuen Top-Level-Objekt
`StackGeometry`.** Die Library beschreibt Komponenten **ohne** räumliche
Ausdehnung in der Zelle; der Stack-Composer wählt + parametrisiert die
Geometrie separat.

### D1 · Schema (`schema/stack_geometry.py`, neu)

```python
@dataclass(frozen=True)
class StackGeometry:
    active_area: Footprint                  # was die Membran active sieht
    overhangs_mm: dict[str, float]          # role → radial overhang in mm
```

- `Footprint` bleibt die existierende Pydantic-Klasse aus `schema/units.py`
  (circular | square | rectangular). Wiederverwendung, keine Duplikation.
- `overhangs_mm` keys: `"anode_bpp"`, `"anode_gdl"`, `"anode_cl"`,
  `"cathode_cl"`, `"cathode_gdl"`, `"cathode_bpp"`. Membrane fehlt
  bewusst — sie *definiert* die active area und hat selbst keinen
  Overhang (sie kann größer sein als die active area, aber der Stack
  rechnet die Membran auf active area = active area).
- Negative Werte verboten (Validator).

### D2 · Defaults (Source-cited)

```python
DEFAULT_GEOMETRY = StackGeometry(
    active_area=Footprint(shape="square",
                          width=Quantity(50, "mm"),
                          height=Quantity(50, "mm")),
    overhangs_mm={
        "anode_cl":    0.0,    # CL ≈ membrane active area (coated within)
        "cathode_cl":  0.0,
        "anode_gdl":   2.0,    # +2 mm radial: typisch 1-5 mm (Rost 2022 setup)
        "cathode_gdl": 2.0,
        "anode_bpp":   25.0,   # +25 mm radial: sealing surface + bolting
        "cathode_bpp": 25.0,
    },
)
```

Active-area-Quelle: **Rost et al. 2022** (Fuel Cells 22:284-289,
DOI 10.1002/fuce.202200068) — 25 cm² Square ist die kanonische
benchtop-Test-Cell-Konvention. Eingetragen in `sources.bib` als
`@rost2022fuelcells`.

Overhang-Werte: aus demselben Test-Cell-Setup (BPP-Plattenformat ~10×10 cm
um 5×5 cm aktive Fläche, GDL +1–2 mm zur Dichtung). Markiert als
`confidence: "convention"` in der ADR — keine Werterfindung, sondern
übliche Lab-Praxis.

### D3 · Code-Auswirkungen

| Datei | Änderung |
|---|---|
| `schema/component.py` | `footprint` Field entfernen (clean cut). |
| `schema/stack_geometry.py` | NEU: `StackGeometry` + `DEFAULT_GEOMETRY`. |
| `geometry/extruded.py` | Signatur ändert auf `build_extruded(component, footprint)` — Footprint wird von außen reingereicht. |
| `geometry/stack_assembly.py` | Neues Kwarg `geometry: StackGeometry`. Pro Layer wird Footprint aus `active_area` + `overhangs_mm[role]` aufgebaut (radial geweitet). |
| `ui/stack_composer.py` | Neues Sub-Panel **`StackGeometryPanel`** (eigene Datei) — 1 Active-Area-Picker (shape+size) + 6 Overhang-Spinner pro Role. Emittiert `geometry_changed`. MainWindow leitet an Re-Compute + Re-Export weiter. |
| `library/components/*.json` | `footprint:` Block aus allen Einträgen entfernt. |
| Tests | `test_geometry_extruded.py`, `test_geometry_stack_assembly.py` an neue Signatur anpassen. Neue Tests für `StackGeometry`-Validierung + Overhang-Berechnung. |

### D4 · Overhang-Logik

Active area = `width × height` (square/rectangular) oder `π·(d/2)²`
(circular). Pro Layer wird die active-area-Form übernommen und um
`overhangs_mm[role]` radial geweitet:

- Square `w×h` → `(w + 2·overhang) × (h + 2·overhang)`.
- Circular `d` → `d + 2·overhang`.
- Rectangular `w×h` → wie square.

Layer-Footprint ist also **dieselbe Form** wie active area, nur größer.
Mischformen (square BPP um circular Membran) sind v1.x.

### D5 · Migration

**Clean cut, v0.2.0 als Minor-Bump** (breaking schema change). Library-
JSONs werden in einem einzigen Commit aufgeräumt; alte Files ohne
Migration-Layer. Begründung: keine externen User, kein Migrations-
Aufwand gerechtfertigt.

Schema-Validierung erzwingt Konsistenz (Pydantic). Wer ältere JSONs
versucht zu laden, kriegt eine klare Pydantic-Fehlermeldung mit dem
übrigen `footprint`-Feld als „extra forbidden".

---

## Rejected Alternatives

| # | Alternative | Verworfen weil |
|---|---|---|
| A1 | Bei Component-Level-Footprint bleiben, Library mit Stufen-Defaults füllen | Stimmt fachlich nicht — Footprint ist Stack-Convention. Wir würden für jede Cell-Größe duplizierte Library-Einträge brauchen. |
| A2 | Single global overhang für alle non-active Layer | Verliert Realismus (BPP ≫ GDL ist physikalisch echt). User hat explizit per-role gewählt. |
| A3 | Deprecate `Component.footprint` schrittweise (v0.1.x → v0.2.0) | Overhead ohne Nutzen — keine externen User. |
| A4 | Square 25 cm² ohne zitierte Quelle nehmen | Strict-Quellen-Verstoß. Rost 2022 ist die Quelle. |
| A5 | Membrane mit eigenem Overhang (z. B. +5 mm) | Membran *ist* per Definition die active area. Membran-Übermaß für Dichtung ist ein Test-Cell-Detail, das v1.x als optionales `membrane_overhang_mm` ergänzt werden kann. |

---

## Consequences

### Positiv
- Schema spiegelt physikalische Realität: Komponenten sind Material-
  Spezifikationen, Geometrie ist Stack-Composition.
- STEP-Export aus ADR-008 wird sofort sichtbar gestuft (BPP > GDL >
  Membrane), ohne Code-Änderung in `stack_assembly`.
- UI-Konfigurierbarkeit ohne neue Library-Einträge: User kann seine
  eigene Test-Cell-Größe modellieren.
- Sources.bib bekommt einen weiteren Anker (Rost 2022) — relevant für
  weitere v1.x-Validierungen.

### Negativ / akzeptierte Trade-offs
- **Breaking change**: Library-JSONs der v0.1.x-Form sind inkompatibel.
  Versionsbump auf 0.2.0. CHANGELOG-Hinweis.
- Per-role Overhang ist 6 Spinner im UI = mehr Cognitive Load. Mitigation:
  Sektion „Geometry" ist einklappbar; Defaults stehen sofort.
- Validation-Badge (UX-VISION §6.4) zeigt aktuell keine Geometry-Validierung.
  Out-of-scope; v1.x-Feature wenn jemals nötig.

---

## Test-Plan

1. **Schema:** `StackGeometry` rejects negative overhang, requires all 6 roles.
2. **Schema:** Component without `footprint` lädt; mit `footprint` (Altform) → Pydantic error.
3. **Geometry:** `build_extruded(comp, footprint=square 50)` → 50×50×thickness Box.
4. **Assembly:** Default geometry → BPP-Layer ist 100×100 mm, GDL 54×54, Membrane 50×50.
5. **Assembly:** Custom overhangs durchgereicht.
6. **Sidecar:** JSON enthält `stack_geometry`-Block mit `active_area` + `overhangs_mm`.
7. **Integration:** Roundtrip Library laden → Default-Stack bauen → STEP exportieren ohne Fehler.

---

## Referenzen

- `library/sources.bib` → `@rost2022fuelcells` (NEU).
- ADR-002 §Strict-Quellen.
- ADR-006 `StackSelection`.
- ADR-008 `StackAssembly`.
- UX-VISION §1 (Stack Design) — Geometry-Sektion ist heute implizit.
