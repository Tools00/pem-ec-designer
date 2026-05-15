# ADR-005 — LCOH-Modell: amortisierte CapEx + OpEx + Strom · Schmidt-2017-Stil

**Status:** Accepted
**Datum:** 2026-05-16
**Vorgänger:** ADR-001 (Scope: „grobe LCOH-Schätzung · Drin v1.0"), ADR-004 (Physics)
**Nachfolger:** —

---

## Context

UX-VISION §4 (Economics) verlangt eine **LCOH-Zahl im Hauptfenster** —
direkt unter der V–I-Kurve, live, ohne Tab-Wechsel. Persona „Tech-Sales /
Consultant" braucht „eine LCOH-Zahl fürs Kundengespräch"; Persona
„Master-Student" muss die Sensitivität gegenüber Strompreis und CapEx
verstehen.

Was **nicht** gebraucht wird: ein vollwertiges techno-ökonomisches Modell
mit Stack-Replacement, Degradation, Steuern, Förder-Mechanismen. Das ist
ein eigenes Tool (Aspen, IRENA-Modelle) und nicht der Wertbeitrag dieses
Designers.

---

## Decision

**Levelised Cost of Hydrogen wird als Annuitäten-Modell mit drei
Komponenten implementiert:**

```
LCOH [€/kg] = (CapEx · CRF + OpEx_fix) / kg_yr_pro_kW
            + SEC_system [kWh/kg] · Strompreis [€/kWh]
```

mit
- `CRF = i (1+i)^n / ((1+i)^n − 1)` (Capital Recovery Factor)
- `SEC_cell = 33.33 kWh/kg / η_LHV` (LHV/M_H2 = 33.33 kWh/kg)
- `SEC_system = SEC_cell / η_BoP`
- `kg_yr_pro_kW = CF · 8760 / SEC_system`
- `η_LHV = V_LHV_thermoneutral / V_cell` aus `physics/efficiency.py`

Defaults (`LCOHInputs()`):

| Parameter | Default | Quelle |
|---|---|---|
| CapEx | 1100 €/kW | Schmidt 2017 §3 (current-state PEM) |
| Strompreis | 50 €/MWh | UX-VISION §4 Default |
| OpEx fix | 3 % CapEx/yr | Schmidt 2017 §3.3 |
| Lifetime | 25 y | Schmidt 2017 baseline |
| Discount | 8 % | Schmidt 2017 baseline (WACC PEM-EC) |
| Capacity Factor | 90 % | Grundlast-Annahme |
| η_BoP | 0.93 | Rectifier + Aux, Schmidt 2017 |

---

## Validation-Anker

Schmidt 2017 (DOI 10.1016/j.ijhydene.2017.10.045) berichtet für
**current-state PEM** ein LCOH-Band von **4–6 €/kg bei 60 €/MWh**. Bei
unserem Default-Strompreis 50 €/MWh verschiebt sich das Band um
≈ 0.5 €/kg nach unten → **3.5–5.5 €/kg**. Unser Modell liefert bei
η_LHV = 0.65 (V_cell ≈ 1.93 V) einen Wert in diesem Band. Test:
`tests/test_lcoh.py::test_lcoh_matches_schmidt_2017_band`.

---

## Rejected Alternatives

### A · Vollwertige LCC mit Stack-Replacement und Degradation

**Variante:** zusätzliche Felder `replacement_year`, `replacement_fraction`,
`degradation_uV_per_h` mit zeitabhängiger V(t).

**Verworfen weil:**
- Verdoppelt Modellkomplexität für ≤ 10 % Genauigkeitsgewinn bei der
  „Sales-Quick-Look"-Persona.
- Verlangt Annahmen (Wann genau ersetzen? Welches Komponentenset?), die
  ohne Stack-Composer (ADR-006) sowieso nicht differenziert beantwortbar
  sind.
- Kann jederzeit additiv ergänzt werden, ohne dass die jetzige API
  bricht — `LCOHInputs` ist ein Dataclass mit Defaults.

### B · System-Boundary inkl. Wasseraufbereitung, Kompression, Speicher

**Verworfen weil:** Pro Persona ist der relevante System-Schnitt
unterschiedlich. „Ab Werk H₂ bei Anodendruck" ist die ehrlichste
gemeinsame Basis. Wer Kompression rein-rechnen will, kann den OpEx-Anteil
manuell erhöhen.

### C · Monte-Carlo-Sensitivität direkt in der Hauptberechnung

**Verworfen weil:** UI-Live-Slider sind die ehrlichere Sensitivitäts-UI.
Wer mehr braucht, scripted gegen `levelised_cost_of_hydrogen()` direkt.

### D · Faradaic-Efficiency < 1 (Crossover-Verlust)

**Verworfen weil:** Bei p_H2 ≤ 30 bar (Slider-Range) ist der Crossover-
Verlust < 2 % und im Rauschen der CapEx-Unsicherheit (≥ ±20 %).

---

## Consequences

### Positiv

- **Live-Slider** in §4 (CapEx + Strompreis) recompute LCOH in < 1 ms.
  Keine Numerik-Tricks nötig.
- **Eine** importierbare Funktion (`levelised_cost_of_hydrogen`), die
  jede Persona verstehen kann, ohne Aspen-Erfahrung.
- Default-Anker `LCOHInputs()` reproduziert die Schmidt-2017-Zahl —
  Vertrauensbildung im ersten Slider-Drag.
- Komponenten-Breakdown im `LCOHResult` (CapEx / OpEx / Strom) macht
  sichtbar, **wo** das €/kg herkommt — passt zur Waterfall-Sprache aus §3.

### Negativ

- Stack-Replacement-Realität (typ. alle 10 y, 30–50 % CapEx) wird in
  v1.0 ignoriert → tendenziell zu optimistische LCOH bei langer
  Lifetime. Akzeptiert, weil im Anker-Band.
- Single design-point V_cell als Lifetime-Mittel → keine Sichtbarkeit
  für Degradations-Effekt. Akzeptiert (siehe A).
- BoP als Konstante 0.93 → keine T-/j-Abhängigkeit. In v1.0 OK,
  in v1.x als `bop_curve(j)` nachrüstbar.

---

## File-Layout

```
src/pem_ec_designer/physics/
├── efficiency.py        ← η_LHV(V), η_HHV(V), SEC(V)
└── lcoh.py              ← LCOHInputs, LCOHResult,
                          ├── capital_recovery_factor()
                          └── levelised_cost_of_hydrogen()

tests/
├── test_efficiency.py   ← 9 Tests
└── test_lcoh.py         ← 14 Tests inkl. Schmidt-Anker
```

UI-Anbindung folgt im selben Commit-Block: `ui/economics_panel.py` +
Hook in `MainWindow._recompute_polarisation`.

---

## Referenzen

- Schmidt 2017, IJHE, `@schmidt2017ijhe` (already in `library/sources.bib`)
- UX-VISION §4 (Economics-Panel-Spec)
- ADR-004 §0-D-Modell (Voraussetzung für η_LHV)
