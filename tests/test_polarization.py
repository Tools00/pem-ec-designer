"""ADR-004 validation: V(j) end-to-end, including Bernt 2016 anchor."""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.physics.ohmic import OhmicContribution
from pem_ec_designer.physics.polarization import (
    CellKinetics,
    OperatingPoint,
    cell_voltage,
    polarisation_curve,
)


# ── Helpers ─────────────────────────────────────────────────────────


def _bernt2016_like_cell() -> tuple[CellKinetics, OperatingPoint, list[OhmicContribution]]:
    """Reconstruct a cell broadly matching Bernt 2016 IrO2/TiO2, thin PFSA, 80 °C.

    Values are *plausibility-band* placeholders for the model — they live in
    the test layer so the physics modules stay Library-independent. Once the
    assembly/ layer maps Components → CellKinetics/OhmicContribution, these
    tests will use real Library entries.

    Choices and provenance:
        - OER on IrO2/TiO2: j0 = 1e-2 A/m² (geometric, Carmo 2013 review band
          for state-of-the-art IrO2). α = 0.75 at n=2 reproduces Bernt's
          ≈ 47 mV/dec Tafel slope (47 mV/dec → α·n ≈ 1.5).
        - HER on Pt/C: j0 = 1e3 A/m² (Pt is very fast — Carmo 2013 lists
          orders of magnitude above OER). α = 0.5.
        - Membrane: thin PFSA (~50 µm Nafion 212) at σ = 10 S/m
          (Kusoglu 2017, fully hydrated 80 °C) → ASR ≈ 0.05 Ω·cm².
        - Other layer ASRs: lumped 0.05 Ω·cm² (CL + GDL + BPP + contacts).
        - Total ASR ≈ 0.10 Ω·cm² — typical for optimised research-cell MEAs.
    """
    kinetics = CellKinetics(
        j0_anode=1.0e-2,
        alpha_anode=0.75,
        j0_cathode=1.0e3,
        alpha_cathode=0.5,
    )
    op = OperatingPoint(T=353.15, p_h2=1e5, p_o2=1e5)
    ohmic = [
        OhmicContribution("membrane_n212", asr=5.0e-6),    # 0.050 Ω·cm²
        OhmicContribution("cl_anode", asr=1.5e-6),         # 0.015 Ω·cm²
        OhmicContribution("cl_cathode", asr=0.5e-6),       # 0.005 Ω·cm²
        OhmicContribution("gdl_anode", asr=1.0e-6),        # 0.010 Ω·cm²
        OhmicContribution("gdl_cathode", asr=1.0e-6),      # 0.010 Ω·cm²
        OhmicContribution("bpp_contact", asr=1.0e-6),      # 0.010 Ω·cm²
    ]
    return kinetics, op, ohmic


# ── Structural / sanity tests ──────────────────────────────────────


def test_at_zero_current_v_equals_e_rev() -> None:
    kinetics, op, ohmic = _bernt2016_like_cell()
    p = cell_voltage(j=0.0, kinetics=kinetics, op=op, ohmic=ohmic)
    assert math.isclose(p.v_cell, p.e_rev, abs_tol=1e-9)
    assert p.eta_oer == 0.0
    assert p.eta_her == 0.0
    assert p.eta_ohm == 0.0


def test_v_is_monotonic_in_j() -> None:
    kinetics, op, ohmic = _bernt2016_like_cell()
    j_values = [1.0, 1e2, 1e3, 5e3, 1e4, 2e4]  # A/m²
    curve = polarisation_curve(j_values, kinetics, op, ohmic)
    v = curve.v_array
    assert all(v[i] < v[i + 1] for i in range(len(v) - 1))


def test_T_effect_is_small_without_arrhenius() -> None:
    """Documented model limitation: with constant j0 (no Arrhenius
    temperature-dependence — explicitly out of scope per ADR-004), the
    Nernst entropy term (E_rev ↓ with T) and the BV prefactor (RT/αnF,
    grows with T) roughly cancel between 60 and 80 °C. A future
    j0(T) model would make V decrease with T as observed experimentally.
    Test asserts the cancellation: |ΔV| ≤ 30 mV at 1 A/cm²."""
    kinetics, _, ohmic = _bernt2016_like_cell()
    op_60 = OperatingPoint(T=333.15, p_h2=1e5, p_o2=1e5)
    op_80 = OperatingPoint(T=353.15, p_h2=1e5, p_o2=1e5)
    p_60 = cell_voltage(j=1e4, kinetics=kinetics, op=op_60, ohmic=ohmic)
    p_80 = cell_voltage(j=1e4, kinetics=kinetics, op=op_80, ohmic=ohmic)
    assert abs(p_80.v_cell - p_60.v_cell) <= 0.030, (
        f"V(80°C) = {p_80.v_cell:.3f}, V(60°C) = {p_60.v_cell:.3f} — "
        f"expected small ΔV without Arrhenius j0(T)"
    )


def test_eta_total_property_consistent() -> None:
    kinetics, op, ohmic = _bernt2016_like_cell()
    p = cell_voltage(j=1e4, kinetics=kinetics, op=op, ohmic=ohmic)
    assert math.isclose(
        p.v_cell, p.e_rev + p.eta_total, abs_tol=1e-12
    )


# ── ADR-004 validation anchor: Bernt 2016 ─────────────────────────


def test_bernt2016_voltage_at_1Acm2_in_plausibility_band() -> None:
    """ADR-004 anchor: V(j=1 A/cm² = 1e4 A/m²) at 80 °C should land in
    1.50–1.70 V (Bernt 2016 reported 1.57 V at MEA optimum; we don't have
    Bernt's exact MEA so check the band, not the point)."""
    kinetics, op, ohmic = _bernt2016_like_cell()
    p = cell_voltage(j=1e4, kinetics=kinetics, op=op, ohmic=ohmic)
    assert 1.50 <= p.v_cell <= 1.70, f"V(1 A/cm²) = {p.v_cell:.3f} V outside Bernt band"


def test_carmo2013_voltage_at_2Acm2_in_plausibility_band() -> None:
    """ADR-004 anchor: V(j=2 A/cm² = 2e4 A/m²) at 80 °C should land in
    1.70–2.00 V (Carmo 2013 review states ~1.8 V as typical)."""
    kinetics, op, ohmic = _bernt2016_like_cell()
    p = cell_voltage(j=2e4, kinetics=kinetics, op=op, ohmic=ohmic)
    assert 1.70 <= p.v_cell <= 2.00, f"V(2 A/cm²) = {p.v_cell:.3f} V outside Carmo band"


# ── Error paths ────────────────────────────────────────────────────


def test_negative_current_rejected() -> None:
    kinetics, op, ohmic = _bernt2016_like_cell()
    with pytest.raises(ValueError):
        cell_voltage(j=-1.0, kinetics=kinetics, op=op, ohmic=ohmic)
