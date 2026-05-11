# ADR-004 — Physics-Modell: 0D · steady-state · isotherm · Butler-Volmer

**Status:** Accepted
**Datum:** 2026-05-12
**Vorgänger:** ADR-001 (Scope: „0D-Physik · Drin v1.0")
**Nachfolger:** —

---

## Context

`physics/` ist bisher leer (`__init__.py` mit 1 Zeile). Library hat 18
Components mit zitierten Kinetik- und ohm'schen Werten, Geometry-Layer
generiert STEP-Exports, UI v0 zeigt Komponenten in 3D — aber das eigentliche
**Designer-Ziel** (Polarisationskurven, Effizienz-Waterfall, LCOH-Vergleich
für Komponenten-Kombinationen) ist nicht implementiert.

Bevor die erste Zeile Physik-Code fällt, fixiert dieses ADR **welches**
Modell. Sonst entsteht Drift zwischen erstem Tafel-Hack und späterer
„richtiger" Implementierung.

Scope-Vorgaben aus ADR-001 / CLAUDE.md:
- **Drin v1.0:** 0D-Physik, Desktop-App, Komponenten-Library
- **Draußen v1.0:** CFD, 1D-Fluid, Multi-User, Web-UI

Das ADR konkretisiert „0D-Physik" — die noch viele Optionen offen lässt.

---

## Optionen (5 unabhängige Achsen)

### Achse 1 · Räumliche Dimension

| | Option | Aufwand | Information-Gain | v1.0? |
|---|---|---|---|---|
| **A1** | 0D lumped (V & j skalar pro Zelle) | 1 Funktion pro Verlust-Term | V(j)-Kurve, Komponenten-Vergleich | ✓ |
| A2 | 1D durch Membran-Dicke | ODE-Solver, Wassertransport-Profil | λ(x), Crossover-Detail | ✗ Scope |
| A3 | 2D Kanal+Dicke | Mesh, FEM/FVM | Strömungs-Uniformität | ✗ explizit Scope |

### Achse 2 · Zeit

| | Option | Wofür | v1.0? |
|---|---|---|---|
| **B1** | steady-state | Design-Point-Vergleich, V–I-Kurve | ✓ |
| B2 | transient | dynamische Last (PV/Wind), Start/Stopp | ✗ eigenes Tool |

### Achse 3 · Kinetik-Modell

| | Option | Gleichung | Bereich | Aufwand |
|---|---|---|---|---|
| C1 | Pure Tafel | η = b·log(j/j₀) | j ≫ j₀ | bricht bei j→0 |
| **C2** | Butler-Volmer symmetrisch | η = (RT/αnF)·arsinh(j/2j₀) | gesamter Bereich | 1 Zeile mehr als Tafel |
| C3 | Butler-Volmer asymmetrisch | αₐ ≠ αc | tiefere Genauigkeit | doppelte Parameter, selten zitiert |
| C4 | Marcus-Hush | quantum-tunneling Korrekturen | Forschungs-Detail | Overkill |

### Achse 4 · Ohm'sche Verluste

| | Option | Was | v1.0? |
|---|---|---|---|
| **D1** | Linear-Sum ΣASR_i (Membrane + 2×CL + 2×GDL + 2×BPP + Kontakt) | ein j·R-Term | ✓ — Library liefert genau diese Werte |
| D2 | Spatially resolved (Land/Channel-Konstriktion) | benötigt 2D | ✗ |
| D3 | Springer 1991 σ(λ,T) | Membran-σ als Funktion Hydratation | erst wenn Wassertransport drin (v1.x) |

### Achse 5 · Mass-Transport & Crossover

| Phänomen | Behandlung v1.0 | Begründung |
|---|---|---|
| **Limiting current j_lim** | ignoriert (V→∞ nicht modelliert) | PEM-EC erreicht es typisch nicht bis 6 A/cm² (Bernt 2016) |
| **H₂-Crossover** | separater Metrik-Block, nicht in V(j) | Trinke 2019 hat Formeln, später nachrüstbar |
| **Gas-Bubble-Coverage** | ignoriert | Vogt-Modell empirisch, trimmt nur Hoch-j |
| **Thermisches Energie-Balance** | ignoriert (T = User-Input, isotherm) | Stack-Temp-Drift sekundär für V–I-Design |
| **Druckabhängigkeit von j₀** | ignoriert | sekundär, ΔE_p im E_rev reicht |
| **Degradation** | reine Lebensdauer-Annahme in LCOH | Maintenance-Modell out of scope |

---

## Decision

**A1 · B1 · C2 · D1 + Mass-Transport explizit ignoriert.**

Konkret:

```
V_cell(j) = E_rev(T, p)
          + η_OER(j; j0_OER, α_a, T)
          + η_HER(j; j0_HER, α_c, T)
          + j · Σ ASR_i
```

mit Butler-Volmer in symmetrischer Form:

```
η_i(j) = (RT / α_i · n · F) · arsinh(j / 2 · j0_i)
```

und E_rev über Nernst-Korrektur:

```
E_rev(T, p) = E_rev_298 + (∂E/∂T)·(T-298) + (RT/2F)·ln(p_H2·p_O2^0.5 / a_H2O)
```

---

## Begründung — warum diese Wahl

1. **Scope-Match.** „0D-Physik" ist gesetzt (ADR-001). Innerhalb davon
   ist Lumped + steady-state + isotherm das minimale Modell, das alle
   in der Library kuratierten Werte tatsächlich nutzt und einen
   nachvollziehbaren V(j)-Output liefert. Komponenten-Designer ≠
   Forschungs-Solver.

2. **Butler-Volmer statt pure Tafel.** Tafel ist Hoch-j-Limit von BV.
   Implementierungskosten identisch (`asinh` vs `log10`), aber BV
   bleibt physikalisch bei j → 0. Bernt 2016 hat 47 mV/dec Tafel-Fit
   — das wird in BV einfach durch effektives j₀ + α abgebildet, kein
   Parameter-Verlust.

3. **Linear-ASR-Sum statt verteilte Ohm'sche Modellierung.** Die
   Library liefert ASR-Werte pro Komponente. Eine räumlich aufgelöste
   Berechnung würde Bandbreiten-Verteilungen und Kontaktwiderstände
   erfordern, die nicht zitierbar sind → strict-quellen-Verstoß.

4. **Falsifizierbarkeit.** Drei Validation-Punkte aus existierender
   `sources.bib`:
   - **Bernt 2016:** V(1 A/cm²) = 1.57 V @ 80 °C, 11.6 wt% Ionomer →
     OER-Kinetik + ohm'sche Summe.
   - **Carmo 2013:** typische 1.8 V @ 2 A/cm² @ 80 °C → Modell-Bandbreite.
   - **Schmidt 2017:** LCOH ~ 4–6 €/kg @ 50 €/MWh, η_LHV ≈ 0.65 →
     Kosten-Effizienz-Pfad.

   Bei Modell ≠ Daten ist die Diagnose eindeutig: entweder Modell ist
   falsch, oder ein Library-Wert ist falsch. Kein „calibration factor".

5. **Composability.** η_total = Σ η_i mit jedem η_i als pure Funktion
   einer Komponenten-Property → User kann sehen: „die 12 mΩ·cm² meines
   GDL kosten mich X mV bei 1 A/cm²". Genau das macht das Tool zum
   Designer.

6. **Refactor-Pfad nach oben.** Jede Achse kann später einzeln aufgewertet
   werden, ohne den Rest umzuwerfen:
   - C2 → C3 (asymm. BV): einen Parameter pro Elektrode dazu.
   - D1 → D3 (Springer-σ): Membran-Material-Spec erweitern.
   - Achse 5 (Crossover): separater Metrik-Block, V(j) bleibt.

---

## Rejected Alternatives

| Verworfen | Warum |
|---|---|
| C1 (pure Tafel) | bricht bei j → 0, kein API-Vorteil gegenüber BV |
| C3 (asymm. BV) | doppelte Parameter, kaum in Library zitiert, kein Information-Gain im Hoch-j |
| Empirischer Polynomial-Fit V(j) | zero predictive power → defeats Designer-Ziel |
| 1D Membran-Transport | nicht im v1.0-Scope, würde Library um λ(x)-Felder erweitern |
| Thermisches Energiebilanz-Modell | sekundär für V–I-Design, eigene Achse für späteres ADR |
| „Calibration factors" zum Hinrechnen | strict-quellen-Verstoß, Anti-Pattern in Sim-Tools |

---

## Konsequenzen

### Code-Struktur (neuer Layer)

```
src/pem_ec_designer/physics/
├── thermodynamics.py    # E_rev(T, p), Nernst-Korrektur
├── kinetics.py          # butler_volmer(j, j0, alpha, T, n=2)
├── ohmic.py             # ASR-Aggregation aus Stack-Komponenten
├── polarization.py      # cell_voltage(stack, j, T, p) — Master
└── crossover.py         # H₂-Crossover (separat, nicht in V(j))
```

- Pure Functions, keine Klassen-State. NumPy-Arithmetik, vektorisiert.
- **Kein Qt-Import** (per ADR-001 §3.1, `test_no_qt_imports.py` deckt
  ab).
- Inputs strikt SI; UI macht Engineering-Unit-Konversion am Boundary.

### Schema-Erweiterungen, die das Modell auslöst

| Wo | Was fehlt heute | Wann |
|---|---|---|
| `Material` | `j0` (Exchange-Current-Density für Anode/Kathode) | vor `kinetics.py`-Implementierung |
| `Material` | `alpha_transfer` (Symmetriefaktor) | dito |
| `Material` | `tafel_slope` ist optional vorhanden → genügt für Cross-Check | ok |
| `Component` (CL) | `area_specific_resistance` (ASR) | optional, viele CLs nicht zitiert |
| `Component` (BPP) | Kontakt-Widerstand zum GDL | Library-Recherche, Skip wenn nicht zitierbar |

Schema-Änderungen kommen in **eigenem Commit vor** dem jeweiligen
Physics-Modul, nicht inline.

### Operating Conditions (UI-Input, nicht Library)

| Größe | Default | Range |
|---|---|---|
| T (cell temp) | 80 °C | 50–95 °C |
| p_anode (O₂) | 1 bar | 1–30 bar |
| p_cathode (H₂) | 1 bar | 1–60 bar |
| j_min / j_max für V–I-Kurve | 0.001 / 6.0 A/cm² | log-Spread |

### Out of Scope für `physics/` (klar markiert)

- **Thermisches Energiebalance.** T ist User-Input. Falls später
  relevant → eigenes Modul `thermal.py`, eigenes ADR.
- **Crossover-Feedback auf V(j).** `crossover.py` rechnet H₂-Flux,
  aber V(j) bleibt unabhängig. Falls Crossover-induzierte V-Drop
  modelliert werden soll → eigenes ADR.
- **Stack-Effekte über Einzelzelle hinaus.** N Zellen × V_cell ist
  trivial; nicht-uniforme Stromverteilung über Stack-Länge ist
  out-of-scope.

---

## Validation

Test-Targets (alle in `tests/test_physics_*.py`):

- [ ] `E_rev(298, 1bar)` = 1.229 ± 0.001 V (CODATA-/Lehrbuch)
- [ ] `E_rev(353, 1bar)` ≈ 1.184 V (Tabellenwert Newman 2021)
- [ ] `butler_volmer(j=1e-7, j0=1e-7, α=0.5, T=353)` ≈ 0 V (j ≈ j₀ → η klein)
- [ ] `butler_volmer(j=1e4 A/m², j0=1e-7, α=0.5, T=353)` ≈ Tafel-Limit
- [ ] `cell_voltage(...)` rekonstruiert Bernt 2016 V(1 A/cm²) = 1.57 ± 0.05 V
  (Toleranz weil Bernt's Werte für ein spezifisches MEA gelten, das
  wir nicht 1:1 in der Library haben — Plausibilitätsband, nicht Punkt)

---

## Quellen

- **Newman & Balsara 2021** — Standard für BV-Form und Nernst-Korrektur (`newman2021em`)
- **Carmo et al. 2013** — Review-Werte für j₀, α, ASR-Bandbreiten (`carmo2013ijhe`)
- **Bernt & Gasteiger 2016** — primärer Validation-Punkt OER-Kinetik (`bernt2016jes`)
- **Trinke et al. 2019** — Crossover-Formeln für späteres Modul (`trinke2019jes`)
- **Smolinka & Garche 2021** — LCOH-Methodik, BoP-Effizienz (`smolinka2021h2`)
- **Schmidt et al. 2017** — LCOH-Target (`schmidt2017ijhe`)
