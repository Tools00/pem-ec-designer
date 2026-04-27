"""Foundation layer: physical constants and unit conversions.

Per ADR-001 §3.1: this layer must NEVER import any UI framework.
Pure functions, fully testable without Qt/Pydantic.
"""

from .constants import (
    AVOGADRO,
    CODATA_VERSION,
    ELECTRON_CHARGE,
    FARADAY,
    GAS_CONSTANT,
    STANDARD_PRESSURE,
    STANDARD_TEMPERATURE,
)
from .units import (
    SI_BASE,
    convert_to_si,
    si_to,
)

__all__ = [
    "AVOGADRO",
    "CODATA_VERSION",
    "ELECTRON_CHARGE",
    "FARADAY",
    "GAS_CONSTANT",
    "STANDARD_PRESSURE",
    "STANDARD_TEMPERATURE",
    "SI_BASE",
    "convert_to_si",
    "si_to",
]
