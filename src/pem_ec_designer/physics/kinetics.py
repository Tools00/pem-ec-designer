"""Electrode kinetics — Butler-Volmer overpotential (symmetric form).

ADR-004 §Decision C2: symmetric Butler-Volmer is used for both OER
(anode) and HER (cathode). Tafel is its high-j limit; sticking with BV
keeps the result physical at j → 0 (where Tafel would diverge) without
adding parameters.

Symmetric BV form solved for η:
    j = 2 · j0 · sinh( α · n · F · η / (R · T) )
    η = (R · T / (α · n · F)) · arsinh( j / (2 · j0) )

Convention:
    - Both η_OER and η_HER are returned as positive numbers.
    - Caller adds them to E_rev with a single global sign in
      polarization.py — this module is responsibility-pure.

Inputs in SI: j and j0 in A/m², T in K, α and n dimensionless.
"""

from __future__ import annotations

import math

from ..foundation.constants import FARADAY, GAS_CONSTANT


def butler_volmer_overpotential(
    j: float,
    j0: float,
    alpha: float,
    T: float,
    n: int = 2,
) -> float:
    """Magnitude of activation overpotential η for one electrode.

    Args:
        j:     current density in A/m².
        j0:    exchange current density in A/m² (same SI base as j).
        alpha: charge-transfer coefficient (dimensionless, 0 < α ≤ 1).
        T:     temperature in K.
        n:     electrons transferred per reaction event (default 2,
               i.e. per H2 molecule produced; for the elementary HER
               or OER half-reactions this would be 1 or 4 — but at the
               cell level the kinetics literature reports j0 already
               normalised to the n=2 overall reaction).

    Returns:
        |η| in volts. Always non-negative.

    Raises:
        ValueError: invalid parameters (T ≤ 0, j0 ≤ 0, α not in (0,1]).

    Notes:
        - At j ≪ j0: BV linearises to η ≈ (RT/αnF)·(j/2j0). Tiny η.
        - At j ≫ j0: BV → Tafel: η ≈ (RT/αnF)·ln(j/j0). Tafel slope
          b = (RT·ln10)/(αnF) ≈ 70 mV/dec at α=0.5, n=2, T=353 K.
        - The factor 2 inside arsinh is the symmetric-BV convention,
          not a Tafel-fit. Removing it would change the j → 0 limit but
          leave the Tafel limit unchanged.
    """
    if T <= 0:
        raise ValueError(f"T must be > 0 K, got {T}")
    if j0 <= 0:
        raise ValueError(f"j0 must be > 0 A/m², got {j0}")
    if not (0 < alpha <= 1):
        raise ValueError(f"alpha must be in (0, 1], got {alpha}")
    if n <= 0:
        raise ValueError(f"n must be > 0, got {n}")

    j_abs = abs(j)
    return (GAS_CONSTANT * T) / (alpha * n * FARADAY) * math.asinh(j_abs / (2.0 * j0))


def tafel_slope(alpha: float, T: float, n: int = 2) -> float:
    """Tafel slope b = (RT·ln10) / (α·n·F) in V/decade.

    For α = 0.5, n = 2, T = 353 K → b ≈ 0.0701 V/dec (≈ 70 mV/dec).
    For α = 0.5, n = 1, T = 353 K → b ≈ 0.140 V/dec.

    Useful for cross-checking Library kinetic parameters against the
    Tafel slopes reported in source papers (e.g. Bernt 2016: 47 mV/dec
    for IrO2/TiO2 — implies α·n ≈ 1.5 at 353 K).
    """
    if T <= 0 or n <= 0 or not (0 < alpha <= 1):
        raise ValueError("invalid parameters")
    return (GAS_CONSTANT * T * math.log(10.0)) / (alpha * n * FARADAY)
