# ADR-006 — Stack-Composer: 9 Library-Filter-Dropdowns + Re-Build on Change

**Status:** Accepted
**Datum:** 2026-05-17
**Vorgänger:** ADR-001 (Komponenten-Library · Drin v1.0), ADR-002 (Library-Layout), ADR-004 (Physics-Inputs), ADR-005 (LCOH)
**Nachfolger:** —

---

## Context

Bis v0.0.1 baut `MainWindow._build_default_stack()` einen **hardcoded**
Referenz-Stack (Nafion 212 + IrO₂ + Pt + 2× SGL 39BB + POCO AXF-5Q).
Das war eine bewusste v0-Abkürzung — es widerspricht aber dem Toolnamen:
ein „Designer", in dem man nichts designen kann, ist eine Lüge.

UX-VISION §1 fordert für v1.0 **9 Dropdowns**:
- 7 Komponenten (Membrane · Anode-CL · Cathode-CL · Anode-GDL · Cathode-GDL · Anode-BPP · Cathode-BPP)
- 2 Katalysator-Materialien (Anoden- + Kathoden-Katalysator)

Jeder Dropdown muss aus der Library kommen, **gefiltert nach Kategorie /
Eigenschaft**. Jede Auswahl-Änderung löst sofort einen Re-Build der
Polarisationskurve + LCOH aus (P2 „Live everywhere").

---

## Decision

**`StackComposer` ist ein eigener `QGroupBox` mit 9 `QComboBox`-Dropdowns.**

- Listen werden beim Konstruieren aus der Library gefiltert. Filter-Logik
  lebt in **`assembly/library_filter.py`** (pure, ohne Qt), damit sie
  testbar bleibt und nicht in der UI vergraben wird.
- Jeder Dropdown emittiert ein gemeinsames Signal
  `selection_changed`, das MainWindow an `_recompute_polarisation` hängt.
- Defaults entsprechen dem bisherigen Hardcoded-Stack — User sieht beim
  ersten Öffnen **dieselbe** V–I-Kurve wie vorher (P7 „Default ist
  sinnvoll", kein leerer Bildschirm).
- `_build_default_stack` wird zu `_build_stack_from_composer` —
  liest die Selektion via `composer.current_selection()` und ruft das
  bestehende `assembly.stack.build_stack()` damit auf. **Keine Änderung
  in `assembly/stack.py`** — der war bereits für Optional-Kwargs gebaut.

### Filter-Spezifikation (`assembly/library_filter.py`)

| Funktion | Kriterium | Resultat |
|---|---|---|
| `membranes(lib)` | `Component.category == "membrane"` | sortiert nach `thickness` |
| `anode_catalyst_layers(lib)` | `category == "anode_cl"` | sortiert nach `id` |
| `cathode_catalyst_layers(lib)` | `category == "cathode_cl"` | sortiert nach `id` |
| `gas_diffusion_layers(lib)` | `category == "gdl"` | sortiert nach `thickness` |
| `bipolar_plates(lib)` | `category == "bpp"` | sortiert nach `id` |
| `membrane_materials(lib)` | `Material.sigma_S_per_m is not None` | sortiert nach `id` |
| `anode_catalyst_materials(lib)` | `Material.j0_anode is not None` | sortiert nach `id` |
| `cathode_catalyst_materials(lib)` | `Material.j0_cathode is not None` | sortiert nach `id` |

Anode-/Cathode-GDL teilen sich denselben Pool — die Library kennzeichnet
nicht „Anoden-GDL vs. Kathoden-GDL" als Felder. Der User wählt frei.

---

## Rejected Alternatives

### A · Drag-&-Drop-Stack-Builder mit visueller Schichtreihenfolge

**Verworfen weil:**
- Komplexer Widget-Code (Drag-Source/Drop-Target, Animations)
- Geometrie der PEM-Zelle ist **fix** (Anode → MEA → Cathode), nicht
  permutierbar. Reihenfolge ist keine Designentscheidung.
- 1 Session Aufwand wird zu 3+ ohne klaren Nutzen.

### B · JSON-Editor für vollständige Schema-Edit-Möglichkeit in der UI

**Verworfen weil:** widerspricht ADR-002 (Library bleibt JSON + Git).
Strict-Quellen-Prinzip funktioniert nur, wenn Werte in versionierten
Dateien leben. UI darf Auswahl, nicht Erfindung.

### C · Tree-Selector statt 9 Flat-Dropdowns

**Verworfen weil:** 9 Items in einer Hierarchie zu rendern verschwendet
Vertikalplatz, ohne Information zu komprimieren. Flat-Form (FormLayout
links Label, rechts ComboBox) ist die seit Jahrzehnten bewährte Lösung.

### D · Auswahl als Pydantic-Model serialisieren und im Hintergrund haben

**Verworfen für v1.0** — die `composer.current_selection()` Methode
liefert ein einfaches Dataclass; Serialisierung wartet auf das v1.x
`.pemcell`-Projekt-File-Format (siehe UX-VISION §13.1).

---

## Consequences

### Positiv

- **Tool wird seinem Namen gerecht.** Personas „Master-Student" und
  „Tech-Sales" können ab jetzt unterschiedliche Stacks vergleichen.
- Backend `assembly.stack.build_stack()` bleibt unverändert — UI-Refactor
  ohne Physik-Risiko.
- Filter-Modul ist **rein**, testbar ohne Qt.
- Skipped-Layer-Indikator (UX-VISION §1) bleibt Pfad C+ — die Diagnostik
  fließt schon jetzt in die Statusbar via `StackBuild.skipped_layers`.

### Negativ

- Bei nur **1 BPP** in der Library ist das BPP-Dropdown faktisch
  Read-only. Akzeptiert — wir füllen die Library inkrementell (Pfad A).
- Anode- und Cathode-GDL-Dropdowns ziehen aus demselben Pool. Bis die
  Library „anode_gdl"-/„cathode_gdl"-Kategorien differenziert, ist das
  technisch korrekt aber inhaltlich grob. Schritt-für-Schritt in Pfad A.
- State-Persistenz (UX-VISION §9 `stack.*` QSettings-Keys) ist Pfad C+ —
  nach App-Restart fällt der Composer auf Defaults zurück.

---

## File-Layout

```
src/pem_ec_designer/
├── assembly/
│   ├── stack.py             ← unverändert
│   └── library_filter.py    ← NEU: 8 reine Filter-Funktionen
├── ui/
│   ├── stack_composer.py    ← NEU: QGroupBox mit 9 Dropdowns
│   └── main_window.py       ← _build_default_stack → composer-driven

tests/
└── test_library_filter.py   ← NEU: Filter-Korrektheit + Sort-Ordnung
```

---

## Referenzen

- UX-VISION §1 (Stack-Sektion)
- UX-VISION §12 Roadmap-Mapping: §1-Dropdowns → Pfad I
- ADR-002 (Library-Architektur)
- ADR-004 §StackBuild
