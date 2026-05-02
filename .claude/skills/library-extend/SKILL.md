---
name: library-extend
description: Extend the pem-ec-designer component library with new specs (GDL/BPP/CL/FF/etc.). Enforces Strict-Quellen, datasheet-first sourcing, peer-reviewed cross-references with DOI, and schema-aware JSON. Use when the user wants to add components, manufacturers, or sources to library/.
---

# library-extend — pem-ec-designer Library-Erweiterung

Du erweiterst die Komponenten-Library dieses Projekts. Halte dich strikt an die folgende Reihenfolge und die Projekt-Regeln.

## 0. Bootstrap (immer zuerst)

1. `cat docs/STATUS.md` — aktueller Stand, was schon drin ist, offene Pfade.
2. `git log --oneline -5` — letzte Commits.
3. `cat CLAUDE.md` — Verhaltensregeln (Visuell statt Prosa, Senior-Mindset, Strict-Quellen, kein Commit ohne OK).
4. `ls library/components/` — welche Kategorien existieren.
5. `cat library/sources.bib | grep '^@' | head -30` — welche BibTeX-Keys schon da sind.

## 1. Frage den User visuell, was hinzukommen soll

Nutze eine Tabelle (Kategorie × Aufwand × Quellenlage), keine Prosa. Beispielspalten:
- Kategorie (gdl/bpp/anode_cl/cathode_cl/flow_field/endplate/gasket/membrane/material)
- Konkrete Items (z.B. „Toray TGP-H -030/-090/-120")
- Aufwand (min)
- Quellenlage (Datasheet schon zitiert? Paper nötig? Recherche-Risiko?)

## 2. Quellen-Disziplin (Strict-Quellen, ADR-002 D4)

**Niemals Werte erfinden.** Wenn ein Wert nicht aus einer Quelle kommt:
- Frag den User nach Datasheet/Paper, oder
- Setze das Feld auf `null` und dokumentiere im JSON-Note, oder
- Lass das Feld weg.

Quellen-Hierarchie (höchste zuerst):
1. **Manufacturer-Direct** Datasheet/White-Paper (URL muss `<vendor>.com` sein, nicht `fuelcellstore.com` etc.)
2. **Peer-reviewed** mit DOI (`@article` mit `doi = {...}`)
3. **Buch** mit ISBN (`@book`, ISBN verifizieren)
4. **Mirror** (fuelcellstore, fuelcellearth) — nur wenn Original verschwunden, mit Note

Bevor du eine BibTeX-Quelle anlegst:
- ISBN/DOI **online verifizieren** (WebSearch + WebFetch). Nicht aus dem Gedächtnis.
- Veröffentlichungsjahr stimmt? Manchmal sind Erscheinungsdaten 1 Jahr off vom Verlagsfront — gegen Verlagsshop-URL prüfen.
- Autorenliste vollständig?

Häufige Halluzinations-Fallen (real passiert in diesem Projekt):
- 2. Auflage erfunden, die nie erschienen ist
- ISBN ausgedacht
- Jahr verwechselt (Smolinka 2021 ↔ 2022)

## 3. Schema kennen, bevor du JSON schreibst

`src/pem_ec_designer/schema/component.py` ist die Wahrheit. Liste der Komponentenklassen:
- `Membrane`, `AnodeCatalystLayer`, `CathodeCatalystLayer`, `GasDiffusionLayer`,
  `BipolarPlate`, `FlowField`, `Endplate`, `Gasket`

**Vor dem Schreiben einer JSON-Spec:** Schema-Klasse lesen, die für die Kategorie zuständig ist. Welche Felder existieren, welche sind required, welche optional?

Wenn ein Feld fehlt, das du brauchst: **STOP.** Nicht ad-hoc in JSON werfen — das löst Pydantic `extra="forbid"` Validation-Errors aus. Stattdessen:
1. Schema erweitern (component.py)
2. Falls neue Unit nötig: foundation/units.py erweitern
3. Tests anpassen (test_schema.py, test_units.py)
4. **Erst dann** JSON schreiben

Diese „Schema-First"-Disziplin ist erprobt — wurde im Mai 2026 nach einem Premature-Scale-Out-Fehler etabliert (Commit `ce5a43f`).

## 4. JSON-Konventionen

- **Hierarchical IDs:** `<category>.<vendor>.<product>` (z.B. `gdl.toray.tgph060`).
- **Units in `Quantity.unit`:** Nur Strings, die in `foundation/units.py:_TO_SI` registriert sind. Konvention: caret für Potenzen (`m^2`, `cm^2`, `g/cm^3`), Mittelpunkt `·` für Produkt (`ohm·m`, `W/(m·K)`).
- **`SourcedValue.source`:** BibTeX-Key, der in `library/sources.bib` existiert.
- **`confidence`:** `"datasheet"` für Hersteller, `"paper"` für peer-reviewed, `"estimate"`/`"guess"` nur mit Note, warum.
- **`cross_references`:** Liste von `{source, note}` für peer-reviewed Sekundär-Quellen, die Datasheet-Werte unabhängig validieren oder Diskrepanzen zeigen (siehe `gdl.toray.tgph060` für Aquah-2024-μCT-Beispiel).
- **`note`-Felder:** Nutze sie, wenn ein Wert eine Bedingung hat (Compression, RT, „>130°", „<13" Spec-Bound).

## 5. Verifikations-Loop

Nach jeder Änderung:
```bash
PYTHONPATH=src pytest -q
```
Muss grün sein. Wenn rot: NICHT weitermachen, NICHT mehr Specs einfügen — erst Schema/Units fixen.

Smoke-Test der Library:
```bash
PYTHONPATH=src python -c "
from pem_ec_designer.materials.loader import load_library
lib = load_library('library')
print(f'Components: {len(lib.components)}, Sources: {len(lib.sources)}')
"
```

## 6. Commit-Disziplin

- **Niemals committen ohne explizites User-OK** (CLAUDE.md, harte Regel).
- Bisect-fähig: wenn Schema + Library zusammen geändert werden, **2 Commits** in dieser Reihenfolge:
  1. `feat(schema): ...` — Schema/Units/Tests
  2. `feat(library): ...` — JSON-Specs + neue BibTeX-Einträge
- Conventional Commits, deutsche Notes erlaubt aber Subject auf Englisch.
- Co-Authored-By trailer.

## 7. Token-Hygiene

- **Nicht auto-lesen:** `docs/decisions/*.html`, `docs/mockups/*.html`, `library/schema.json` (groß, generiert).
- Bei großen Files: `Read` mit `offset/limit`.
- Web-Recherche pro neuer Quelle in 1-2 parallelen WebSearches bündeln, nicht seriell.

## 8. Default-Pfade (wenn User nichts angibt)

Empfehle in dieser Reihenfolge, weil zahlt-direkt-auf-UI ein:
1. **GDL-Vertiefung:** Toray TGP-H -030/-090/-120 + SIGRACET 22 BB/28 BC/36 BB (Datasheets bereits zitiert, reines Tipparbeit, ~20 min)
2. **BPP:** POCO AXF-5Q, Schunk FU 4369 (neue Datasheets nötig)
3. **Anode CL:** IrO₂-Loadings aus Bernt 2018/2020 (Papers schon in sources.bib)
4. **Flow Field:** Channel-Standardvarianten (geometry-only, eigene Konvention)

## 9. Nicht in deiner Verantwortung (Scope-Grenzen)

- Keine 0D-Physik in dieser Skill (separate Skill / Session).
- Keine UI-Änderungen.
- Keine Geometry-Generator-Erweiterungen.
- Keine ADRs schreiben (separate Diskussion mit User).

## 10. Session-Ende

- STATUS.md aktualisieren (Tabelle „Stand", Pfade, Tests-Count).
- Offene Punkte für Folgesession explizit benennen.
- Kein Commit ohne OK.
