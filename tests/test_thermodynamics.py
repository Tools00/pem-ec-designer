"""ADR-004 validation: E_rev(T, p) targets."""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.physics.thermodynamics import reversible_voltage


def test_standard_state_returns_codata_value() -> None:
    """At 25 °C, 1 bar, E_rev must be 1.229 V (Faraday × CODATA ΔG)."""
    e = reversible_voltage(T=298.15)
    assert math.isclose(e, 1.229, abs_tol=1e-3)


def test_80C_matches_newman_table() -> None:
    """At 80 °C, 1 bar, E_rev ≈ 1.183 V (textbook tabulated)."""
    e = reversible_voltage(T=353.15)
    assert math.isclose(e, 1.183, abs_tol=2e-3)


def test_higher_T_lowers_E_rev() -> None:
    """dE/dT < 0 — gas-product entropy term reduces the reversible
    voltage as T rises."""
    e_low = reversible_voltage(T=298.15)
    e_high = reversible_voltage(T=358.15)  # 85 °C
    assert e_high < e_low


def test_higher_pH2_raises_E_rev() -> None:
    """Nernst: higher product pressure → higher E_rev (energy penalty
    to compress H2 against external pressure)."""
    e_1bar = reversible_voltage(T=353.15, p_h2=1e5, p_o2=1e5)
    e_30bar = reversible_voltage(T=353.15, p_h2=30e5, p_o2=1e5)
    assert e_30bar > e_1bar
    # Magnitude check: (RT/2F)·ln(30) ≈ 0.0518 V at 353 K
    expected_delta = (8.314 * 353.15) / (2 * 96485) * math.log(30.0)
    assert math.isclose(e_30bar - e_1bar, expected_delta, rel_tol=1e-3)


def test_zero_T_rejected() -> None:
    with pytest.raises(ValueError):
        reversible_voltage(T=0)


def test_negative_pressure_rejected() -> None:
    with pytest.raises(ValueError):
        reversible_voltage(T=353.15, p_h2=-1.0)
