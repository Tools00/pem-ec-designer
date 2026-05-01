# ADR-003 — Qt-Binding: PySide6 (LGPL)

**Status:** Accepted
**Datum:** 2026-05-01
**Vorgänger:** ADR-001 (Framework-Wahl, hat die Frage offen gelassen)
**Nachfolger:** —

---

## Context

ADR-001 hat „PyQt6 oder PySide6" gewählt und die Binding-Frage explizit
in ein späteres ADR vertagt (siehe ADR-001 §Risiken/Lizenz). Vor dem
ersten UI-Code muss diese Wahl stehen — sobald Widgets gegen ein
konkretes Binding geschrieben sind, ist Wechsel zwar API-kompatibel,
aber dennoch Reibung (Imports, Slot-Decorators, Signal-Syntax).

**Drift-Signal:** `pyproject.toml` listet bereits `PySide6` im
`[project.optional-dependencies].ui`-Block, **nicht** PyQt6. Faktisch
ist die Wahl schon getroffen worden, aber undokumentiert.

### Scope-Trennung (wichtig)

Dieses ADR beantwortet **nur Frage 1**:

1. **Qt-Binding-Lizenz** — bestimmt, ob das Produkt proprietär
   verkauft werden kann.
2. ~~Produkt-Lizenz-System~~ (FlexLM-Aktivierung etc.) — **out of
   scope**, weit entfernt, eigenes ADR wenn jemals relevant.

ADR-001 hatte beide Fragen unter „ADR-003 Lizenz-System" gebündelt —
Auflösung: Frage 1 hier, Frage 2 separat (oder nie).

---

## Optionen

| | Binding | Lizenz | Konsequenz für Produkt-Lizenz |
|---|---|---|---|
| **A** | PyQt6 | GPLv3 oder kommerziell (Riverbank, ~£550/Dev/Jahr) | Produkt MUSS GPL sein, sonst kostenpflichtige Lizenz |
| **B** | PySide6 | LGPLv3 | Produkt frei wählbar (proprietär möglich, wenn dynamisch gelinkt) |

Beide Bindings nutzen dasselbe Qt6 darunter, sind API-kompatibel zu
~95 %, beide werden aktiv gepflegt. Funktional kein Unterschied für
diesen Use-Case.

`pyvistaqt` unterstützt beide. `build123d` ist Qt-frei (eigene Viewer
über VTK / OCP), also kein Konflikt.

---

## Decision

**Option B: PySide6 (LGPLv3).**

---

## Begründung

1. **Optionalität.** LGPL erlaubt sowohl GPL- als auch proprietäre
   Distribution. PyQt6 verbaut die proprietäre Option ohne Cash.
   Persona-Mix laut ADR-001 (Portfolio + späteres Industrie-Tool)
   verträgt keine voreilige GPL-Selbstbindung.
2. **Drift bereinigen.** `pyproject.toml` hat schon `PySide6` —
   diese ADR formalisiert nur, was de facto gilt.
3. **Switching-Kosten ≈ 0.** API-kompatibel; falls Qt for Python
   einmal stagniert, ist Wechsel auf PyQt6 mechanisch (Imports,
   `pyqtSignal` ↔ `Signal`).
4. **Offizieller Qt-Binding.** PySide6 wird von der Qt Company
   selbst gepflegt — minimal stabilere Roadmap als der
   community-gepflegte PyQt6.

---

## Konsequenzen

- **UI-Code-Konvention:** ausschließlich `from PySide6.…`. Lint-Regel
  oder Import-Test erzwingt das (siehe „Validation").
- **CI:** PySide6 nur im `[ui]`-Extra installieren — Headless-Tests
  bleiben Qt-frei (ADR-001 §3.1, durch `test_no_qt_imports.py`
  abgesichert).
- **Distribution:** Bei Binary-Release (PyInstaller etc.) sicherstellen,
  dass Qt dynamisch gelinkt wird (Standard bei PySide6-PyInstaller-Build).
  LGPL-Pflicht: User muss Qt austauschen können → kein static link.
- **Lizenz-Datei:** `LICENSE` des eigenen Codes bleibt frei wählbar
  (TBD; nicht Teil dieses ADR). `THIRD_PARTY_LICENSES.md` muss Qt-LGPL
  und PySide6-LGPL listen vor erstem Release.

---

## Risiken

- **PyInstaller + PySide6 + macOS arm64:** bekannte Edge-Cases bei
  Code-Signing. Risiko → vor v0.5 (erstes Binary-Release) Smoke-Test.
- **LGPL „dynamic linking"-Klausel** in Python-Welt nicht 100 %
  juristisch geklärt — Qt-Company bestätigt aber Python-Dynamic-Import
  als LGPL-konform. Quelle: <https://www.qt.io/qt-licensing>.

---

## Validation

- [ ] `pyproject.toml` führt **nur** PySide6 unter `[ui]`, kein PyQt6.
- [ ] CI-Job oder Pre-Commit prüft: kein `PyQt6`-Import in `src/`.
- [ ] `THIRD_PARTY_LICENSES.md` existiert spätestens vor v0.5.
- [ ] ADR-001 referenziert dieses ADR als Auflösung der Binding-Frage.

---

## Quellen

- ADR-001 §Risiken („PySide vs. PyQt-Lizenz")
- Qt for Python licensing: <https://wiki.qt.io/Qt_for_Python>
- Qt licensing overview: <https://www.qt.io/qt-licensing>
- Riverbank PyQt commercial: <https://www.riverbankcomputing.com/commercial/pyqt>
