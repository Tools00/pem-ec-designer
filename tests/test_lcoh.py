"""Tests for physics/lcoh.py — Levelised Cost of Hydrogen.

Validation anchor: Schmidt 2017 (DOI 10.1016/j.ijhydene.2017.10.045).
Current-state PEM-EC ≈ 4–6 €/kg at 1100 €/kW · 50 €/MWh · CF 90 % ·
lifetime 25 y · i = 8 % · η_LHV ≈ 0.65.
"""

from __future__ import annotations

import pytest

from pem_ec_designer.physics.efficiency import lhv_efficiency
from pem_ec_designer.physics.lcoh import (
    LCOHInputs,
    capital_recovery_factor,
    levelised_cost_of_hydrogen,
)


# ── CRF ────────────────────────────────────────────────────────────────


def test_crf_zero_discount_is_inverse_lifetime() -> None:
    assert capital_recovery_factor(0.0, 25) == pytest.approx(1 / 25)


def test_crf_schmidt_2017_baseline() -> None:
    # i = 8 %, n = 25 y → CRF ≈ 0.0937
    assert capital_recovery_factor(0.08, 25) == pytest.approx(0.0937, abs=1e-4)


def test_crf_higher_discount_means_higher_crf() -> None:
    assert capital_recovery_factor(0.10, 25) > capital_recovery_factor(0.05, 25)


@pytest.mark.parametrize("bad_n", [0, -1, -10])
def test_crf_rejects_non_positive_lifetime(bad_n: int) -> None:
    with pytest.raises(ValueError):
        capital_recovery_factor(0.08, bad_n)


def test_crf_rejects_negative_discount() -> None:
    with pytest.raises(ValueError):
        capital_recovery_factor(-0.01, 25)


# ── LCOH ───────────────────────────────────────────────────────────────


def test_lcoh_matches_schmidt_2017_band() -> None:
    """Anchor: 3.5–5.5 €/kg at Schmidt 2017 current-state parameters.

    eta_LHV = 0.65 (V_cell ≈ 1.93 V, typical PEM at 1.5 A/cm², 80 °C,
    Nafion 212, IrO2 anode). Schmidt 2017 Fig. 5 reports 4–6 €/kg at
    60 €/MWh; at 50 €/MWh the band shifts down ~0.5 €/kg → 3.5–5.5 €/kg.
    """
    eta = 0.65
    result = levelised_cost_of_hydrogen(eta, LCOHInputs())
    assert 3.5 < result.lcoh_total < 5.5, f"LCOH {result.lcoh_total} outside Schmidt band"


def test_lcoh_components_sum_to_total() -> None:
    result = levelised_cost_of_hydrogen(0.7, LCOHInputs())
    summed = result.capex_component + result.opex_component + result.electricity_component
    assert result.lcoh_total == pytest.approx(summed)


def test_lcoh_electricity_dominates_at_reference_case() -> None:
    """At 50 €/MWh and ~70 % eta, electricity is the dominant cost."""
    result = levelised_cost_of_hydrogen(0.7, LCOHInputs())
    assert result.electricity_component > result.capex_component
    assert result.electricity_component > result.opex_component


def test_lcoh_falls_as_efficiency_rises() -> None:
    a = levelised_cost_of_hydrogen(0.60, LCOHInputs()).lcoh_total
    b = levelised_cost_of_hydrogen(0.70, LCOHInputs()).lcoh_total
    c = levelised_cost_of_hydrogen(0.80, LCOHInputs()).lcoh_total
    assert a > b > c


def test_lcoh_rises_with_electricity_price() -> None:
    cheap = LCOHInputs(electricity_eur_per_mwh=30.0)
    expensive = LCOHInputs(electricity_eur_per_mwh=80.0)
    a = levelised_cost_of_hydrogen(0.7, cheap).lcoh_total
    b = levelised_cost_of_hydrogen(0.7, expensive).lcoh_total
    assert b > a


def test_lcoh_rises_with_capex() -> None:
    cheap = LCOHInputs(capex_eur_per_kw=600.0)
    expensive = LCOHInputs(capex_eur_per_kw=2000.0)
    a = levelised_cost_of_hydrogen(0.7, cheap).lcoh_total
    b = levelised_cost_of_hydrogen(0.7, expensive).lcoh_total
    assert b > a


def test_lcoh_falls_with_capacity_factor() -> None:
    """Higher CF amortises CapEx over more kg → CapEx component drops."""
    low = LCOHInputs(capacity_factor=0.40)
    high = LCOHInputs(capacity_factor=0.95)
    a = levelised_cost_of_hydrogen(0.7, low)
    b = levelised_cost_of_hydrogen(0.7, high)
    assert a.capex_component > b.capex_component


def test_lcoh_consumes_efficiency_from_lhv_efficiency() -> None:
    """Integration: composing efficiency.lhv_efficiency → LCOH works."""
    v_cell = 1.93
    eta = lhv_efficiency(v_cell)
    result = levelised_cost_of_hydrogen(eta, LCOHInputs())
    assert 3.5 < result.lcoh_total < 5.5


def test_lcoh_sec_system_includes_bop() -> None:
    eta = 0.7
    result_full_bop = levelised_cost_of_hydrogen(eta, LCOHInputs(bop_efficiency=1.0))
    result_partial = levelised_cost_of_hydrogen(eta, LCOHInputs(bop_efficiency=0.90))
    assert result_partial.sec_system_kwh_per_kg > result_full_bop.sec_system_kwh_per_kg


@pytest.mark.parametrize("bad_eta", [0.0, -0.1, 1.6])
def test_lcoh_rejects_nonphysical_efficiency(bad_eta: float) -> None:
    with pytest.raises(ValueError):
        levelised_cost_of_hydrogen(bad_eta, LCOHInputs())


@pytest.mark.parametrize(
    "bad_inputs",
    [
        LCOHInputs(capex_eur_per_kw=-100.0),
        LCOHInputs(electricity_eur_per_mwh=-1.0),
        LCOHInputs(opex_fixed_fraction=-0.01),
        LCOHInputs(capacity_factor=0.0),
        LCOHInputs(capacity_factor=1.1),
        LCOHInputs(bop_efficiency=0.0),
        LCOHInputs(bop_efficiency=1.5),
    ],
)
def test_lcoh_rejects_invalid_inputs(bad_inputs: LCOHInputs) -> None:
    with pytest.raises(ValueError):
        levelised_cost_of_hydrogen(0.7, bad_inputs)
