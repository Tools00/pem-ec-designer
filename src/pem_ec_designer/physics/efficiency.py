"""Efficiency — voltage-based efficiency for PEM water electrolysis.

ADR-004 §0-D · steady · isothermal. Given a cell voltage V_cell, return
the LHV-based electrical efficiency

    η_LHV = V_LHV_thermoneutral / V_cell

where V_LHV = LHV(H2) / (n · F) ≈ 1.253 V (liquid-water reactant,
water-vapour product). This is the convention used in Schmidt 2017 and
most techno-economic studies. HHV-based efficiency is also provided for
completeness — it divides by V_HHV ≈ 1.481 V instead.

Why voltage-based, not energy-balance?
    For 0-D · steady, electrical input per mole H2 = n·F·V_cell
    (charge-conservation, no extra losses booked outside V_cell).
    LHV per mole = LHV_H2 → η_LHV = LHV_H2 / (n·F·V_cell) = V_LHV / V_cell.
    No double-counting against the polarisation curve.

Limits:
    1. Pure cell-level efficiency. BoP (rectifier, compressor, water-
       treatment) auxiliaries are NOT in this number. Realistic system-
       level η is ~5–10 points lower than cell-level. Captured in LCOH
       via a separate `bop_efficiency` factor (see lcoh.py).
    2. Faradaic efficiency assumed 1.0 (no gas crossover). Crossover at
       elevated p_H2 is real but second-order at v1.0 scope.
"""

from __future__ import annotations

from ..foundation.constants import FARADAY, HHV_H2, LHV_H2

# Thermoneutral voltages derived from heating values (n = 2).
# V_LHV  = LHV_H2 / (n·F) = 241 820 / (2·96 485.33212) ≈ 1.2531 V
# V_HHV  = HHV_H2 / (n·F) = 285 830 / (2·96 485.33212) ≈ 1.4813 V
_N_ELECTRONS: int = 2
V_LHV_THERMONEUTRAL: float = LHV_H2 / (_N_ELECTRONS * FARADAY)
V_HHV_THERMONEUTRAL: float = HHV_H2 / (_N_ELECTRONS * FARADAY)


def lhv_efficiency(v_cell: float) -> float:
    """LHV-based cell efficiency.

    Args:
        v_cell: cell voltage in volts. Must be > 0.

    Returns:
        η_LHV = V_LHV / V_cell  (dimensionless, typically 0.6 – 0.8).

    Notes:
        η_LHV > 1 means the cell runs endothermically below the LHV
        thermoneutral point — physically possible but rare for liquid-fed
        PEM-EC, since the actual thermoneutral point is V_HHV ≈ 1.481 V.
    """
    if v_cell <= 0:
        raise ValueError(f"v_cell must be > 0 V, got {v_cell}")
    return V_LHV_THERMONEUTRAL / v_cell


def hhv_efficiency(v_cell: float) -> float:
    """HHV-based cell efficiency. η_HHV = V_HHV / V_cell."""
    if v_cell <= 0:
        raise ValueError(f"v_cell must be > 0 V, got {v_cell}")
    return V_HHV_THERMONEUTRAL / v_cell


def specific_energy_consumption(v_cell: float) -> float:
    """Cell-level electrical input per kg H2 produced, in kWh/kg.

    SEC = n·F·V_cell / M(H2)  →  J/kg  →  /3.6e6 → kWh/kg
    Equivalently SEC = (LHV_H2 / M(H2)) / η_LHV = 33.33 kWh/kg / η_LHV.
    """
    if v_cell <= 0:
        raise ValueError(f"v_cell must be > 0 V, got {v_cell}")
    from ..foundation.constants import MOLAR_MASS_H2

    j_per_kg = _N_ELECTRONS * FARADAY * v_cell / MOLAR_MASS_H2  # J/kg
    return j_per_kg / 3.6e6  # kWh/kg
