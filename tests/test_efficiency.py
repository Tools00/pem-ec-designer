"""Tests for physics/efficiency.py — V_LHV / V_HHV / SEC."""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.physics.efficiency import (
    V_HHV_THERMONEUTRAL,
    V_LHV_THERMONEUTRAL,
    hhv_efficiency,
    lhv_efficiency,
    specific_energy_consumption,
)


def test_v_lhv_thermoneutral_is_1_253_volts() -> None:
    # LHV_H2 / (n·F) = 241 820 / 192 970.66 ≈ 1.2531 V
    assert V_LHV_THERMONEUTRAL == pytest.approx(1.2531, abs=1e-3)


def test_v_hhv_thermoneutral_is_1_481_volts() -> None:
    assert V_HHV_THERMONEUTRAL == pytest.approx(1.4813, abs=1e-3)


def test_lhv_efficiency_at_thermoneutral_voltage_is_one() -> None:
    assert lhv_efficiency(V_LHV_THERMONEUTRAL) == pytest.approx(1.0)


def test_lhv_efficiency_typical_pem_operating_point() -> None:
    # Bernt 2016 reports ~1.7 V at 1 A/cm² → η_LHV ≈ 1.253 / 1.7 ≈ 0.737
    assert lhv_efficiency(1.7) == pytest.approx(0.737, abs=5e-3)


def test_hhv_efficiency_lower_than_lhv() -> None:
    # HHV thermoneutral is higher voltage → η_HHV > η_LHV for V > V_LHV
    v = 1.8
    assert hhv_efficiency(v) > lhv_efficiency(v)


def test_specific_energy_consumption_at_thermoneutral_is_33_3_kwh_per_kg() -> None:
    # SEC(V_LHV) = LHV/M_H2 / 3.6e6 ≈ 33.33 kWh/kg
    assert specific_energy_consumption(V_LHV_THERMONEUTRAL) == pytest.approx(33.33, abs=0.05)


def test_specific_energy_consumption_inversely_proportional_to_eta() -> None:
    v = 1.85
    sec = specific_energy_consumption(v)
    eta = lhv_efficiency(v)
    # SEC · η_LHV = 33.33 kWh/kg  (LHV / M_H2)
    assert sec * eta == pytest.approx(33.33, abs=0.05)


@pytest.mark.parametrize("bad_v", [0.0, -0.1, -1.0])
def test_efficiency_rejects_non_positive_voltage(bad_v: float) -> None:
    with pytest.raises(ValueError):
        lhv_efficiency(bad_v)
    with pytest.raises(ValueError):
        hhv_efficiency(bad_v)
    with pytest.raises(ValueError):
        specific_energy_consumption(bad_v)


def test_efficiency_monotonic_in_voltage() -> None:
    """Higher V_cell → lower efficiency."""
    voltages = [1.5, 1.7, 1.9, 2.1]
    etas = [lhv_efficiency(v) for v in voltages]
    assert all(etas[i] > etas[i + 1] for i in range(len(etas) - 1))
    # Sanity: not NaN, not negative
    assert all(math.isfinite(e) and e > 0 for e in etas)
