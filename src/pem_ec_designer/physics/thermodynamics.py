"""Thermodynamics — reversible cell voltage for PEM water electrolysis.

ADR-004 §Decision: 0D · steady-state · isothermal. T and p are user
inputs; this module computes E_rev(T, p) only.

Reaction (liquid water reactant, gaseous products):
    H2O(l) → H2(g) + 0.5 O2(g)

Reversible voltage at non-standard state:
    E_rev(T, p) = E_rev,298
                + (∂E/∂T)·(T − 298.15)
                + (R·T / (n·F)) · ln(p_H2 · p_O2^0.5 / a_H2O)

with n = 2 (electrons transferred per H2 molecule produced) and
liquid-water activity a_H2O ≈ 1.

Sign of temperature coefficient:
    dE/dT = −ΔS_rxn / (n·F)
ΔS_rxn > 0 (gas products from liquid reactant) → dE/dT < 0
→ E_rev decreases with rising T.

All inputs in SI: T in K, p in Pa.
"""

from __future__ import annotations

import math

from ..foundation.constants import (
    FARADAY,
    GAS_CONSTANT,
    REVERSIBLE_VOLTAGE_25C,
    STANDARD_PRESSURE,
    STANDARD_TEMPERATURE,
)

# Temperature coefficient of E_rev for H2O(l) → H2(g) + 0.5 O2(g).
# Derived from ΔS_rxn at 25 °C:
#   ΔS_rxn = S°(H2) + 0.5·S°(O2) − S°(H2O,l)
#          = 130.68 + 0.5·205.14 − 69.91  =  163.34 J/(mol·K)
# dE/dT  = −ΔS_rxn / (n·F)  =  −163.34 / (2·96 485.33)  ≈  −8.46 × 10⁻⁴ V/K
# Source: standard tabulated entropies (NIST WebBook); cited in Newman 2021.
DE_REV_DT: float = -8.46e-4  # V/K  (n = 2)

# Number of electrons transferred per H2 formed
_N_ELECTRONS: int = 2

# Water activity in PEM-EC (assumed pure liquid water at cathode side
# saturating the membrane). Could be < 1 for partially humidified anode
# inlet but is a second-order correction not in v1.0 scope.
_WATER_ACTIVITY: float = 1.0


def reversible_voltage(
    T: float,
    p_h2: float = STANDARD_PRESSURE,
    p_o2: float = STANDARD_PRESSURE,
) -> float:
    """Reversible (open-circuit) cell voltage for PEM water electrolysis.

    Args:
        T:    cell temperature in Kelvin.
        p_h2: hydrogen partial pressure at cathode in Pascal.
        p_o2: oxygen partial pressure at anode in Pascal.

    Returns:
        E_rev in volts.

    Raises:
        ValueError: T ≤ 0 K or any pressure ≤ 0 Pa.

    Notes:
        At standard state (T = 298.15 K, p_H2 = p_O2 = 1 bar) this returns
        the CODATA-derived value 1.229 V.
        At 353.15 K, p = 1 bar it returns ≈ 1.183 V.
    """
    if T <= 0:
        raise ValueError(f"T must be > 0 K, got {T}")
    if p_h2 <= 0 or p_o2 <= 0:
        raise ValueError(f"pressures must be > 0 Pa, got p_h2={p_h2}, p_o2={p_o2}")

    e_temperature_corrected = REVERSIBLE_VOLTAGE_25C + DE_REV_DT * (T - STANDARD_TEMPERATURE)

    # Nernst term — pressures normalised to STANDARD_PRESSURE
    # because the standard-state E_rev,298 was tabulated at 1 bar.
    q_reaction = (p_h2 / STANDARD_PRESSURE) * math.sqrt(p_o2 / STANDARD_PRESSURE) / _WATER_ACTIVITY
    nernst = (GAS_CONSTANT * T) / (_N_ELECTRONS * FARADAY) * math.log(q_reaction)

    return e_temperature_corrected + nernst
