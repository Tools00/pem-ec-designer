"""ADR-004 validation: ohmic ASR aggregation."""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.physics.ohmic import (
    OhmicContribution,
    asr_from_thickness_and_conductivity,
    ohmic_overpotential,
    total_asr,
)


def test_empty_stack_has_zero_drop() -> None:
    assert total_asr([]) == 0.0
    assert ohmic_overpotential(j=1e4, contributions=[]) == 0.0


def test_series_sum_is_linear() -> None:
    """Layers add in series."""
    contribs = [
        OhmicContribution("membrane", asr=1.5e-5),     # 15 mΩ·cm²
        OhmicContribution("gdl", asr=1.0e-6),          # 1 mΩ·cm²
        OhmicContribution("bpp_contact", asr=5.0e-7),  # 0.5 mΩ·cm²
    ]
    total = total_asr(contribs)
    assert math.isclose(total, 1.65e-5, rel_tol=1e-9)


def test_voltage_drop_scales_linearly_with_j() -> None:
    contribs = [OhmicContribution("test", asr=1.0e-5)]
    eta_low = ohmic_overpotential(j=1e3, contributions=contribs)
    eta_high = ohmic_overpotential(j=2e3, contributions=contribs)
    assert math.isclose(eta_high / eta_low, 2.0, rel_tol=1e-12)


def test_nafion117_at_80C_realistic_asr() -> None:
    """Sanity: 183 µm Nafion at σ = 10 S/m (Kusoglu 2017) → ASR ≈ 1.83e-5 Ω·m² (≈ 0.18 Ω·cm²).
    Cross-check against literature values 0.1-0.2 Ω·cm² for hydrated Nafion 117 at 80 °C."""
    asr = asr_from_thickness_and_conductivity(thickness_m=183e-6, sigma_s_per_m=10.0)
    assert math.isclose(asr, 1.83e-5, rel_tol=1e-6)
    # That is 0.183 Ω·cm² — sits in the literature band 0.1-0.2 Ω·cm².
    asr_ohm_cm2 = asr / 1e-4
    assert 0.10 <= asr_ohm_cm2 <= 0.25


def test_negative_asr_rejected() -> None:
    with pytest.raises(ValueError):
        total_asr([OhmicContribution("bad", asr=-1.0)])


def test_zero_thickness_rejected() -> None:
    with pytest.raises(ValueError):
        asr_from_thickness_and_conductivity(thickness_m=0.0, sigma_s_per_m=10.0)


def test_zero_sigma_rejected() -> None:
    with pytest.raises(ValueError):
        asr_from_thickness_and_conductivity(thickness_m=1e-4, sigma_s_per_m=0.0)


def test_contribution_voltage_drop() -> None:
    """Per-layer voltage drop for waterfall display."""
    c = OhmicContribution("membrane", asr=1.5e-5)
    assert math.isclose(c.voltage_drop(j=1e4), 0.15, rel_tol=1e-9)
