"""Polarisation — full V(j) for a PEM-EC cell. ADR-004 master function.

Composes thermodynamics + kinetics + ohmic:

    V_cell(j) = E_rev(T, p)
              + η_OER(j; j0_anode, α_anode, T)
              + η_HER(j; j0_cathode, α_cathode, T)
              + j · Σ ASR_i

Cell is described by an `OperatingPoint` (T, p_H2, p_O2, j-array) plus
a `CellKinetics` (one j0/α pair per electrode) plus a list of
`OhmicContribution`. None of these are tied to the Library schema yet —
they are plain dataclasses so the physics is testable without Library
loading. The bridge from `Component` + `Material` → these dataclasses
lives in `assembly/` (next iteration).

Return type is `PolarisationCurve` — keeps each loss term broken out,
so the UI can plot a stacked-area decomposition (Devil's-Advocate
question: "where does my 1.7 V at 1 A/cm² actually go?").

Known v1.0 limitations (per ADR-004 §Rejected Alternatives):

1. j0 is treated as temperature-independent. The full Arrhenius form
   j0(T) = j0_ref · exp(−E_a/R · (1/T − 1/T_ref)) is the physically
   correct way to capture how kinetics improve with T. Without it,
   the BV prefactor (RT/αnF) grows linearly with T while E_rev drops
   linearly; the two roughly cancel in the 60–95 °C operating band.
   Real cells show V going down with T because j0 increases
   exponentially — that effect is absent here.
2. ASR is also treated as temperature-independent. Membrane σ
   typically grows ~2 % per K through Nafion's hydration window.
3. No mass-transport limit at high j — V(j) keeps a finite slope
   beyond j_lim instead of curving up sharply.

When a result conflicts with experiment in a way these limitations
predict, fix the model — do not insert a calibration factor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .kinetics import butler_volmer_overpotential
from .ohmic import OhmicContribution, ohmic_overpotential
from .thermodynamics import reversible_voltage


@dataclass(frozen=True)
class CellKinetics:
    """Per-electrode Butler-Volmer parameters."""

    j0_anode: float       # A/m² — OER exchange current density
    alpha_anode: float    # charge-transfer coefficient
    j0_cathode: float     # A/m² — HER exchange current density
    alpha_cathode: float


@dataclass(frozen=True)
class OperatingPoint:
    """Thermodynamic state of the cell."""

    T: float              # K
    p_h2: float           # Pa
    p_o2: float           # Pa


@dataclass(frozen=True)
class PolarisationPoint:
    """All loss terms at a single current density — for waterfall plots."""

    j: float
    e_rev: float
    eta_oer: float
    eta_her: float
    eta_ohm: float
    v_cell: float

    @property
    def eta_total(self) -> float:
        return self.eta_oer + self.eta_her + self.eta_ohm


@dataclass(frozen=True)
class PolarisationCurve:
    """V(j) and its breakdown across a current-density sweep."""

    points: list[PolarisationPoint] = field(default_factory=list)

    @property
    def j_array(self) -> list[float]:
        return [p.j for p in self.points]

    @property
    def v_array(self) -> list[float]:
        return [p.v_cell for p in self.points]


def cell_voltage(
    j: float,
    kinetics: CellKinetics,
    op: OperatingPoint,
    ohmic: list[OhmicContribution],
    n: int = 2,
) -> PolarisationPoint:
    """Single-point V(j) with all loss terms broken out."""
    if j < 0:
        raise ValueError(f"j must be ≥ 0 A/m² (electrolysis convention), got {j}")

    e_rev = reversible_voltage(T=op.T, p_h2=op.p_h2, p_o2=op.p_o2)

    eta_oer = butler_volmer_overpotential(
        j=j, j0=kinetics.j0_anode, alpha=kinetics.alpha_anode, T=op.T, n=n
    )
    eta_her = butler_volmer_overpotential(
        j=j, j0=kinetics.j0_cathode, alpha=kinetics.alpha_cathode, T=op.T, n=n
    )
    eta_ohm = ohmic_overpotential(j=j, contributions=ohmic)

    v_cell = e_rev + eta_oer + eta_her + eta_ohm

    return PolarisationPoint(
        j=j,
        e_rev=e_rev,
        eta_oer=eta_oer,
        eta_her=eta_her,
        eta_ohm=eta_ohm,
        v_cell=v_cell,
    )


def polarisation_curve(
    j_values: list[float],
    kinetics: CellKinetics,
    op: OperatingPoint,
    ohmic: list[OhmicContribution],
    n: int = 2,
) -> PolarisationCurve:
    """V(j) sweep — one PolarisationPoint per j in j_values.

    Pure: no I/O, no plotting. The UI layer plots the result; this layer
    only computes it.
    """
    points = [cell_voltage(j=jv, kinetics=kinetics, op=op, ohmic=ohmic, n=n) for jv in j_values]
    return PolarisationCurve(points=points)
