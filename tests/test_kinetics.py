"""ADR-004 validation: Butler-Volmer kinetics."""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.physics.kinetics import (
    butler_volmer_overpotential,
    tafel_slope,
)


# ── Limits and basic behaviour ────────────────────────────────────


def test_zero_current_zero_overpotential() -> None:
    """j = 0 → η = 0 by definition of equilibrium."""
    eta = butler_volmer_overpotential(j=0.0, j0=1e-3, alpha=0.5, T=353.15)
    assert eta == 0.0


def test_overpotential_is_non_negative() -> None:
    """|η| is returned regardless of j sign."""
    eta_pos = butler_volmer_overpotential(j=1e4, j0=1e-3, alpha=0.5, T=353.15)
    eta_neg = butler_volmer_overpotential(j=-1e4, j0=1e-3, alpha=0.5, T=353.15)
    assert eta_pos > 0
    assert eta_neg == eta_pos


def test_high_current_converges_to_tafel() -> None:
    """At j ≫ j0, BV → η ≈ (RT/αnF) · ln(j/j0). Test within 1 %."""
    j, j0, alpha, T, n = 1e4, 1e-6, 0.5, 353.15, 2
    eta_bv = butler_volmer_overpotential(j=j, j0=j0, alpha=alpha, T=T, n=n)
    eta_tafel = (8.314 * T) / (alpha * n * 96485) * math.log(j / j0)
    assert math.isclose(eta_bv, eta_tafel, rel_tol=1e-2)


def test_low_current_linearises() -> None:
    """At j ≪ j0, η ≈ (RT/αnF) · j/(2 j0). Test within 1 %."""
    j, j0, alpha, T, n = 1e-9, 1e-3, 0.5, 353.15, 2
    eta_bv = butler_volmer_overpotential(j=j, j0=j0, alpha=alpha, T=T, n=n)
    eta_linear = (8.314 * T) / (alpha * n * 96485) * j / (2.0 * j0)
    assert math.isclose(eta_bv, eta_linear, rel_tol=1e-2)


def test_higher_j0_lowers_eta() -> None:
    """Better catalyst (higher j0) → lower overpotential at same j."""
    j, alpha, T = 1e4, 0.5, 353.15
    eta_slow = butler_volmer_overpotential(j=j, j0=1e-7, alpha=alpha, T=T)
    eta_fast = butler_volmer_overpotential(j=j, j0=1e-3, alpha=alpha, T=T)
    assert eta_fast < eta_slow


# ── Tafel-slope cross-check ────────────────────────────────────────


def test_tafel_slope_at_reference_conditions() -> None:
    """α=0.5, n=2, T=353 K → b ≈ 70 mV/dec."""
    b = tafel_slope(alpha=0.5, T=353.15, n=2)
    assert math.isclose(b, 0.0701, abs_tol=2e-4)


def test_bernt2016_inferred_alpha_n_product() -> None:
    """Bernt 2016 reports OER Tafel slope ≈ 47 mV/dec at 80 °C.
    Solve b for α·n: α·n = (R·T·ln10) / (b·F).
    """
    b_bernt = 0.047  # V/dec
    T = 353.15
    alpha_n = (8.314 * T * math.log(10.0)) / (b_bernt * 96485)
    # Expected ≈ 1.49 — implies α·n ≈ 1.5 (e.g. α=0.75, n=2 or α=0.375, n=4)
    assert 1.4 < alpha_n < 1.6


# ── Error paths ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "kwargs",
    [
        {"T": 0.0, "j0": 1e-3, "alpha": 0.5},
        {"T": 353.15, "j0": 0.0, "alpha": 0.5},
        {"T": 353.15, "j0": 1e-3, "alpha": 0.0},
        {"T": 353.15, "j0": 1e-3, "alpha": 1.5},
        {"T": 353.15, "j0": 1e-3, "alpha": 0.5, "n": 0},
    ],
)
def test_invalid_parameters_raise(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        butler_volmer_overpotential(j=1.0, **kwargs)
