"""Round-trip tests for the foundation.units module.

Per ADR-001 §3.2: every supported unit must round-trip without
floating-point drift beyond a sane tolerance.
"""

from __future__ import annotations

import math

import pytest

from pem_ec_designer.foundation.units import (
    convert_temperature,
    convert_to_si,
    si_to,
)

ROUND_TRIP_CASES: list[tuple[float, str]] = [
    (183.0, "um"),
    (0.05, "m"),
    (50.0, "mm"),
    (7.2, "mil"),
    (2.0, "A/cm^2"),
    (200.0, "mA/cm^2"),
    (10.0, "S/m"),
    (0.1, "S/cm"),
    (1.0, "bar"),
    (101_325.0, "Pa"),
    (1100.0, "g/eq"),
    (1.98, "g/cm^3"),
    (50.0, "EUR/cell"),
    # GDL / electrochem additions
    (95.0, "g/m^2"),
    (80.0, "mohm·cm"),
    (5.8, "mohm·cm"),
    (13.0, "mohm·cm^2"),
    (0.56, "ohm·mm"),
    (0.20, "W/(m·K)"),
    (1.7, "W/(m·K)"),
    (1.5, "s"),
    (130.0, "deg"),
    (78.0, "percent"),
    (5.0, "percent_w_w"),
    (8.4e-12, "m^2"),
    (2.0, "mg/cm^2"),
]


# Cross-unit equivalence cases — same physical quantity, different units
# in SI must agree.
EQUIVALENCE_CASES: list[tuple[tuple[float, str], tuple[float, str]]] = [
    # 80 mohm·cm == 8e-4 ohm·m
    ((80.0, "mohm·cm"), (8e-4, "ohm·m")),
    # 13 mohm·cm^2 == 1.3e-6 ohm·m^2
    ((13.0, "mohm·cm^2"), (1.3e-6, "ohm·m^2")),
    # 95 g/m^2 == 0.095 kg/m^2
    ((95.0, "g/m^2"), (0.095, "kg/m^2")),
    # 78 percent == 0.78 fraction
    ((78.0, "percent"), (0.78, "fraction")),
    # 5 percent_w_w == 0.05 fraction
    ((5.0, "percent_w_w"), (0.05, "fraction")),
    # 0.56 ohm·mm == 5.6e-4 ohm·m
    ((0.56, "ohm·mm"), (5.6e-4, "ohm·m")),
    # W/(m.K) (ASCII alias) == W/(m·K)
    ((1.7, "W/(m.K)"), (1.7, "W/(m·K)")),
    # 2 mg/cm² == 0.02 kg/m² (catalyst loading)
    ((2.0, "mg/cm^2"), (0.02, "kg/m^2")),
]


@pytest.mark.parametrize(("a", "b"), EQUIVALENCE_CASES)
def test_unit_equivalence(a: tuple[float, str], b: tuple[float, str]) -> None:
    """Two engineering forms of the same quantity must yield equal SI values."""
    si_a = convert_to_si(*a)
    si_b = convert_to_si(*b)
    assert math.isclose(si_a, si_b, rel_tol=1e-12, abs_tol=1e-18), (
        f"{a} → {si_a} but {b} → {si_b}"
    )


@pytest.mark.parametrize(("value", "unit"), ROUND_TRIP_CASES)
def test_round_trip(value: float, unit: str) -> None:
    """Convert to SI then back — must equal within 1e-12 relative."""
    si = convert_to_si(value, unit)
    back = si_to(si, unit)
    assert math.isclose(back, value, rel_tol=1e-12, abs_tol=1e-15), (
        f"round-trip failed for {value} {unit}: got {back}"
    )


def test_um_and_mm_consistent() -> None:
    """183 µm == 0.183 mm == 1.83e-4 m in SI."""
    a = convert_to_si(183, "um")
    b = convert_to_si(0.183, "mm")
    c = convert_to_si(1.83e-4, "m")
    assert math.isclose(a, b, rel_tol=1e-12)
    assert math.isclose(b, c, rel_tol=1e-12)


def test_unknown_unit_raises() -> None:
    with pytest.raises(ValueError, match="unknown unit"):
        convert_to_si(1.0, "furlong")


def test_celsius_uses_explicit_function() -> None:
    """Celsius is offset, not factor — must go through convert_temperature."""
    with pytest.raises(ValueError, match="convert_temperature"):
        convert_to_si(25.0, "°C")


def test_temperature_celsius() -> None:
    assert math.isclose(convert_temperature(25.0, "°C"), 298.15)
    assert math.isclose(convert_temperature(0.0, "C"), 273.15)


def test_temperature_kelvin_passthrough() -> None:
    assert convert_temperature(298.15, "K") == 298.15
