"""LCOH — Levelised Cost of Hydrogen (€/kg H2).

ADR-005 (LCOH-Modell, Session N+1) — minimal techno-economic wrapper
around the 0-D physics. Computes the discounted average cost of one
kilogram of hydrogen across the plant lifetime, given:

  - cell-level efficiency η_LHV from physics/efficiency.py
  - CapEx specific to nameplate electrical input [€/kW]
  - electricity price [€/MWh]
  - fixed OpEx as fraction of CapEx per year
  - capacity factor (CF), lifetime, discount rate
  - optional Balance-of-Plant efficiency factor (system vs. cell)

Formula (deliberately simple — Schmidt 2017 style):

    LCOH = (CapEx · CRF + OpEx_fixed_per_year) / annual_kg_per_kW
         + SEC_system [kWh/kg] · electricity_price [€/kWh]

with
    CRF = i (1+i)^n / ((1+i)^n − 1)       (capital recovery factor)
    SEC_cell = 33.33 kWh/kg / η_LHV       (LHV / molar-mass conversion)
    SEC_system = SEC_cell / η_BoP
    annual_kg_per_kW = CF · 8760 / SEC_system

Validation anchor (ADR-005 §Validation):
    Schmidt 2017 (DOI 10.1016/j.ijhydene.2017.10.045): current-state
    PEM electrolysis ≈ 4–6 €/kg at 50 €/MWh, CapEx 1100 €/kW, CF 90 %,
    lifetime 25 y, discount 8 %, BoP ≈ 0.93. We must land in this band
    at η_LHV ≈ 0.65 (V_cell ≈ 1.93 V). Tested in test_lcoh.py.

NOT in v1.0 scope (Devil's-Advocate-resistant):
    - Stack-replacement CapEx (typically every 10 y, 30–50 % of CapEx).
      Could be added later as `replacement_fraction` + `replacement_year`.
    - Water cost (~0.01 €/kg, negligible).
    - Variable OpEx (electricity already separate).
    - CO2-price / Green-H2 certificate revenue (model output, not input).
    - Degradation (V_cell drift over lifetime). Use a single design-point
      V_cell as average.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..foundation.constants import LHV_H2, MOLAR_MASS_H2

# 33.327 kWh/kg — LHV-based minimum energy to produce 1 kg H2.
# (LHV_H2 / MOLAR_MASS_H2) / 3.6e6 = 241 820 / 2.01588e−3 / 3.6e6
SEC_LHV_KWH_PER_KG: float = (LHV_H2 / MOLAR_MASS_H2) / 3.6e6


@dataclass(frozen=True)
class LCOHInputs:
    """All economic + system parameters for one LCOH evaluation.

    Defaults match the Schmidt 2017 PEM-EC current-state anchor so that
    LCOHInputs() reproduces the textbook 4–6 €/kg result when paired
    with eta_lhv ≈ 0.65 (V_cell ≈ 1.93 V).
    """

    capex_eur_per_kw: float = 1100.0       # €/kW nameplate — Schmidt 2017
    electricity_eur_per_mwh: float = 50.0  # €/MWh
    opex_fixed_fraction: float = 0.03      # 3 %/yr of CapEx — Schmidt 2017 §3.3
    lifetime_years: int = 25
    discount_rate: float = 0.08            # 8 %/yr — Schmidt 2017 baseline
    capacity_factor: float = 0.90          # CF = 90 %
    bop_efficiency: float = 0.93           # rectifier + auxiliaries, Schmidt 2017


@dataclass(frozen=True)
class LCOHResult:
    """Breakdown of one LCOH evaluation (€/kg)."""

    lcoh_total: float          # €/kg H2
    capex_component: float     # €/kg from amortised CapEx
    opex_component: float      # €/kg from fixed OpEx
    electricity_component: float  # €/kg from grid electricity
    sec_system_kwh_per_kg: float  # system-level specific energy consumption
    annual_kg_per_kw: float    # kg H2 per kW nameplate per year


def capital_recovery_factor(discount_rate: float, lifetime_years: int) -> float:
    """CRF = i (1+i)^n / ((1+i)^n − 1).

    Edge case: i = 0 → CRF = 1/n (limit by L'Hôpital).
    """
    if lifetime_years <= 0:
        raise ValueError(f"lifetime_years must be > 0, got {lifetime_years}")
    if discount_rate < 0:
        raise ValueError(f"discount_rate must be ≥ 0, got {discount_rate}")
    if discount_rate == 0:
        return 1.0 / lifetime_years
    growth = (1.0 + discount_rate) ** lifetime_years
    return discount_rate * growth / (growth - 1.0)


def levelised_cost_of_hydrogen(eta_lhv: float, inputs: LCOHInputs) -> LCOHResult:
    """Levelised cost of hydrogen for one design point.

    Args:
        eta_lhv: LHV-based cell efficiency at the design current density,
                 e.g. from `physics.efficiency.lhv_efficiency(v_cell)`.
        inputs:  economic + system parameters.

    Returns:
        LCOHResult with total and per-component breakdown.

    Raises:
        ValueError on non-physical inputs.
    """
    if not (0.0 < eta_lhv <= 1.5):
        raise ValueError(f"eta_lhv must be in (0, 1.5], got {eta_lhv}")
    if not (0.0 < inputs.bop_efficiency <= 1.0):
        raise ValueError(f"bop_efficiency must be in (0, 1], got {inputs.bop_efficiency}")
    if not (0.0 < inputs.capacity_factor <= 1.0):
        raise ValueError(f"capacity_factor must be in (0, 1], got {inputs.capacity_factor}")
    if inputs.capex_eur_per_kw < 0 or inputs.electricity_eur_per_mwh < 0:
        raise ValueError("CapEx and electricity price must be ≥ 0")
    if inputs.opex_fixed_fraction < 0:
        raise ValueError("opex_fixed_fraction must be ≥ 0")

    sec_cell = SEC_LHV_KWH_PER_KG / eta_lhv                       # kWh/kg, cell-only
    sec_system = sec_cell / inputs.bop_efficiency                 # kWh/kg, with BoP
    annual_kg_per_kw = inputs.capacity_factor * 8760.0 / sec_system  # kg/(kW·yr)

    crf = capital_recovery_factor(inputs.discount_rate, inputs.lifetime_years)
    capex_annual = inputs.capex_eur_per_kw * crf                  # €/(kW·yr)
    opex_annual = inputs.capex_eur_per_kw * inputs.opex_fixed_fraction

    capex_component = capex_annual / annual_kg_per_kw             # €/kg
    opex_component = opex_annual / annual_kg_per_kw               # €/kg

    # Electricity: €/MWh → €/kWh × kWh/kg = €/kg
    electricity_component = (inputs.electricity_eur_per_mwh / 1000.0) * sec_system

    total = capex_component + opex_component + electricity_component
    return LCOHResult(
        lcoh_total=total,
        capex_component=capex_component,
        opex_component=opex_component,
        electricity_component=electricity_component,
        sec_system_kwh_per_kg=sec_system,
        annual_kg_per_kw=annual_kg_per_kw,
    )
