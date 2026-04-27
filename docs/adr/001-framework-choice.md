# ADR-001 — Framework-Wahl: PyQt + pyvistaqt + build123d

**Status:** Accepted
**Datum:** 2026-04-27
**Vorgänger:** keiner (erstes ADR im Projekt)
**Nachfolger:** ADR-002 (Library-Architektur), ADR-003 (Lizenz-System, Late Binding)

---

## Context

`pem-ec-designer` ist Projekt 2 im `Simulation-tools/`-Workspace. Vorläufer
`pem-ec-0d` ist auf v0.6 eingefroren und liefert die 0D-Elektrochemie-Physik.
Dieses Projekt soll daraus einen **echten visuellen Designer** mit
3D/CAD-Stack-Konstruktion machen.

Vor dem ersten Code-Commit verlangt `Simulation-tools/CLAUDE.md` und
`docs/simulation-project-framework.md`, dass ein Framework-ADR
geschrieben wird. Ohne dieses ADR ist kein Scaffold (`pyproject.toml`,
`src/`, `requirements.txt`) erlaubt — das war der Kardinalfehler in
`pem-ec-0d` (siehe `docs/lessons/pem-ec-0d.md`, Strukturfehler #1).

### Vorgelagerte Entscheidungen

Library-Scope (`docs/decisions/001-library-scope.html`):

| Frage | Wahl |
|---|---|
| Q1 Form | C · Python-Package + build123d |
| Q2 Quellen | Strict — Paper-Pflicht |
| Q3 Sprache | Hybrid — EN-Specs / DE-UI |
| Q4 Umfang | Wide 60+ Komponenten |

ADR-001 Klärungs-Resultat (`docs/decisions/003-adr-conflicts.html`):

| Frage | Antwort |
|---|---|
| K1 Persona primär | Du selbst (Portfolio) |
| K1 Persona sekundär | Simulation-Engineer |
| K2 Multi/Desktop | Desktop bleibt · Single-User |
| K3 18M-State | Industrie-Tool (Lizenz-Anspruch) |
| K4 Physik-Domänen | Elektrochemie + Thermodynamik + 0D-Fluid + Kosten |

### Restspannung (bewusst akzeptiert)

Persona „Portfolio" + 18M-State „Industrie-Tool" sind klassisch
gegensätzlich (Demo-Stück vs. Produkt). Auflösung: AVL-/Comsol-Modell —
Desktop-Native mit späterem Lizenz-Layer. Lizenz-System wird als
**ADR-003 Late Binding** gemerkt und nicht in v0.1 implementiert.

---

## Decision

**UI-Framework:** **PyQt6** (oder PySide6 als API-kompatible Alternative)
**3D-Engine:** **pyvistaqt** (PyVista im Qt-Widget) + **build123d** (CAD-Geometrie)
**Verteilung:** Native Desktop-App, später cross-platform Builds
(macOS/Windows/Linux) via PyInstaller oder briefcase.

### Begründung

1. **3D-Anforderung CAD-Qualität (1.4):** Browser-Stacks (NiceGUI, Panel)
   können three.js-Meshes anzeigen, aber kein nativer STEP/STL-Export.
   `build123d` produziert OCCT-Geometrie, die in pyvistaqt direkt als
   VTK-Mesh angezeigt und unverlustig als CAD-File exportiert werden kann.
2. **Single-User Desktop (K2):** Web-Stacks würden Server-Deploy + Auth
   erzwingen — beides nicht gewollt.
3. **Industrie-Tool 18M (K3):** Konkurrenz (AVL Boost, Comsol, Ansys
   Discovery) sind ebenfalls Desktop-First mit Lizenz-Layer. PyQt ist
   in dieser Klasse Standard.
4. **Lange Berechnungen >5s (1.5):** PyQt hat erprobte Background-Worker
   (`QThread`, `QtConcurrent`) — kein Celery/RabbitMQ-Setup nötig.
5. **Persona „Simulation-Engineer" sekundär (K1):** erwartet volle
   Parameter-Kontrolle, Tabbed Workspaces, dockable Panels. Das ist
   PyQts Heimatdomäne; in Browser-UIs wäre's Eigenbau.

---

## Consequences

### Positiv

- CAD-Qualität nativ. Echte STEP/STL-Files lieferbar.
- Lizenz-System (ADR-003) später einbaubar (FlexLM-Pattern, Online-Activation).
- Plugin-Architektur via Qt-Plugins möglich, falls Erweiterungen für
  andere Stacks (Brennstoffzelle, Redox-Flow) später kommen.
- Performance: native GPU-Rendering, keine WebGL-Begrenzung.
- Großes Ökosystem: pyvistaqt, qtconsole, pyqtgraph, qtawesome.

### Negativ

- **Kein Browser-Demo möglich.** Portfolio-Pitch braucht Screencast +
  Binary-Download — Hürde gegenüber Streamlit-Cloud-Link.
  Mitigation: zusätzlich GIF-Demos und Web-Mockup auf GitHub Pages.
- **Cross-Platform-Builds sind Arbeit.** Windows-MSI, macOS-DMG, Linux-AppImage
  müssen separat gepflegt werden. CI-Setup nötig spätestens v0.5.
- **build123d-Lock.** Wechsel auf CadQuery oder Open CASCADE direkt
  später teuer. Risiko mittel (build123d ist aktiv gepflegt, OCP-basiert).
- **PySide vs. PyQt-Lizenz.** PyQt6 ist GPL/Commercial. Wenn Industrie-Tool
  proprietär verkauft werden soll, ist **PySide6 (LGPL)** die korrektere
  Wahl. Verschoben in ADR-003 (Lizenz-System).
- **Mobile-/Web-Reach = 0.** Manager-Persona (in K1 abgewählt) kann das
  Tool nicht im Browser anschauen. Bewusst akzeptiert.

### Neutral

- Erste echte Python-Dependency-Liste entsteht jetzt. Ab Commit dieses
  ADRs ist `pyproject.toml`-Scaffold erlaubt (siehe `CLAUDE.md`).

---

## Layer-Struktur (verbindlich)

Nach `simulation-project-framework.md` §3.1, angepasst auf PyQt:

```
src/pem_ec_designer/
├── ui/                       # PyQt6-Code, Widgets, Layouts
│   └── (framework-spezifisch — bei Framework-Wechsel rewriten)
├── visualization/            # pyvistaqt-Wrapper, build123d→VTK-Bridge
│   └── (library-spezifisch)
├── assembly/                 # Stack-Composition (Geometrie + Physik)
│   └── (framework-agnostisch — voll testbar ohne Qt)
├── physics/                  # Pure Functions, von pem-ec-0d adaptiert
│   ├── electrochem.py        # Butler-Volmer, Nernst, Tafel
│   ├── thermo.py             # Wärmebilanz, ΔG/ΔH
│   ├── fluid.py              # Darcy-Weisbach (0D)
│   └── cost.py               # CAPEX/OPEX/LCOH
├── materials/                # Library-Loader (Pydantic), components.json
├── foundation/
│   ├── constants.py          # CODATA 2018
│   └── units.py              # SI ↔ Engineering, Round-Trip-Tests
└── __init__.py
```

**Verbindlich:** `import pem_ec_designer.physics` muss ohne installiertes
PyQt funktionieren. Smoke-Test in `tests/test_no_qt_imports.py` ab v0.1.

---

## Alternatives Considered

| Framework | Warum verworfen |
|---|---|
| **NiceGUI** | Browser-Demo wäre Portfolio-Vorteil, aber Multi-User unklar gewollt (K2 = Single-User Desktop). Auch: Web-3D via three.js kann kein nativer STEP-Export. |
| **Panel + pyvista** | Ähnlich Browser-Stack, weniger ausgereiftes 3D als pyvistaqt-native. |
| **Streamlit / Dash** | 3D-Anforderung CAD-Qualität schließt aus. |
| **FastAPI + React + three.js** | Massiver Mehraufwand für Single-User-Desktop. Erst sinnvoll wenn K2 = Web-Multi gewählt wird (war nicht der Fall). |
| **Jupyter + ipywidgets + k3d** | Kein Deploy-Pfad zu Industrie-Tool (K3). Bleibt Exploration-Toolkit, wird ggf. in v0.x für interne Validation-Notebooks genutzt. |

---

## Validation des ADRs

Dieses ADR ist abgesegnet, wenn folgende Smoke-Tests funktionieren
(spätestens v0.1):

- [ ] `python -c "import pem_ec_designer.physics"` läuft ohne PyQt-Install
- [ ] `python -c "from build123d import Box; Box(1,1,1).export_step('t.step')"` produziert valide STEP
- [ ] `python -m pem_ec_designer` öffnet leeres PyQt-MainWindow ohne Crash
- [ ] `pyvistaqt.QtInteractor` rendert einen Test-Cube in unter 2 s

---

## References

- `Simulation-tools/docs/simulation-project-framework.md` §1, §2, §3
- `Simulation-tools/docs/lessons/pem-ec-0d.md` — Strukturfehler #1, #3
- `pem-ec-designer/docs/decisions/001-library-scope.html`
- `pem-ec-designer/docs/decisions/002-framework-adr.html`
- `pem-ec-designer/docs/decisions/003-adr-conflicts.html`
- build123d: <https://build123d.readthedocs.io/>
- pyvistaqt: <https://qtdocs.pyvista.org/>
- PySide6 vs PyQt6 Lizenz: <https://wiki.qt.io/Qt_for_Python>
