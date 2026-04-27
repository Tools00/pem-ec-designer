"""Unit conversions — SI ↔ engineering units.

Per ADR-001 §3.2: internal storage is always SI. Engineering units are
allowed only at the IO boundary (UI input, JSON specs). All conversion
goes through this module. Round-trip tests in tests/test_units.py.

Convention: convert_to_si(value, unit) returns SI float.
            si_to(value, unit) returns engineering float from SI.
"""

from __future__ import annotations

# Mapping: engineering unit string → multiplier to SI base
# SI base unit per quantity is implied by the conversion factor.
_TO_SI: dict[str, tuple[float, str]] = {
    # length
    "m":   (1.0,    "m"),
    "cm":  (1e-2,   "m"),
    "mm":  (1e-3,   "m"),
    "um":  (1e-6,   "m"),
    "µm":  (1e-6,   "m"),
    "nm":  (1e-9,   "m"),
    "mil": (2.54e-5, "m"),     # 1 mil = 25.4 µm
    "in":  (2.54e-2, "m"),
    # area
    "m^2":   (1.0,   "m^2"),
    "cm^2":  (1e-4,  "m^2"),
    "mm^2":  (1e-6,  "m^2"),
    # current density
    "A/m^2":  (1.0,   "A/m^2"),
    "A/cm^2": (1e4,   "A/m^2"),
    "mA/cm^2":(10.0,  "A/m^2"),
    # conductivity
    "S/m":   (1.0,    "S/m"),
    "S/cm":  (100.0,  "S/m"),
    # area-specific resistance
    "ohm·m^2":   (1.0,   "ohm·m^2"),
    "Ω·m^2":     (1.0,   "ohm·m^2"),
    "ohm·cm^2":  (1e-4,  "ohm·m^2"),
    "Ω·cm^2":    (1e-4,  "ohm·m^2"),
    # pressure
    "Pa":   (1.0,    "Pa"),
    "kPa":  (1e3,    "Pa"),
    "MPa":  (1e6,    "Pa"),
    "bar":  (1e5,    "Pa"),
    "psi":  (6894.757, "Pa"),
    # temperature: special-cased (offset, not multiplier) — see _convert_T
    # mass
    "kg":  (1.0,    "kg"),
    "g":   (1e-3,   "kg"),
    "mg":  (1e-6,   "kg"),
    # density
    "kg/m^3": (1.0,   "kg/m^3"),
    "g/cm^3": (1e3,   "kg/m^3"),
    # equivalent weight
    "g/eq":  (1e-3, "kg/eq"),
    "kg/eq": (1.0,  "kg/eq"),
    # money: passed through, no conversion (annotated for clarity)
    "EUR":         (1.0, "EUR"),
    "EUR/cell":    (1.0, "EUR/cell"),
    "EUR/m^2":     (1.0, "EUR/m^2"),
    "EUR/kg":      (1.0, "EUR/kg"),
    "EUR/kW":      (1.0, "EUR/kW"),
    "EUR/kWh":     (1.0, "EUR/kWh"),
    "USD":         (1.0, "USD"),
    "USD/cell":    (1.0, "USD/cell"),
}

# Canonical SI base per known engineering unit (used by si_to to invert)
SI_BASE: dict[str, str] = {u: base for u, (_, base) in _TO_SI.items()}


def convert_to_si(value: float, unit: str) -> float:
    """Convert an engineering value+unit to SI float.

    Raises ValueError if unit is unknown (no silent fall-through).

    Temperature must be passed in K. Celsius/Fahrenheit go through
    convert_temperature() because they are offset-based.
    """
    if unit in ("K", "kelvin"):
        return float(value)
    if unit in ("°C", "C", "degC", "celsius"):
        raise ValueError(
            "Use convert_temperature(value, 'C') for celsius — "
            "offset-based, not factor-based."
        )
    if unit not in _TO_SI:
        raise ValueError(f"unknown unit: {unit!r}. Add to units._TO_SI.")
    factor, _ = _TO_SI[unit]
    return float(value) * factor


def si_to(value_si: float, target_unit: str) -> float:
    """Convert an SI value to a target engineering unit."""
    if target_unit in ("K", "kelvin"):
        return float(value_si)
    if target_unit not in _TO_SI:
        raise ValueError(f"unknown unit: {target_unit!r}.")
    factor, _ = _TO_SI[target_unit]
    if factor == 0:
        raise ZeroDivisionError(f"unit {target_unit!r} has factor 0")
    return float(value_si) / factor


def convert_temperature(value: float, from_unit: str) -> float:
    """Convert a temperature reading to Kelvin."""
    if from_unit in ("K", "kelvin"):
        return float(value)
    if from_unit in ("°C", "C", "degC", "celsius"):
        return float(value) + 273.15
    if from_unit in ("°F", "F", "degF", "fahrenheit"):
        return (float(value) - 32.0) * 5.0 / 9.0 + 273.15
    raise ValueError(f"unknown temperature unit: {from_unit!r}")
