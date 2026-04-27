"""Quantity = {value, unit}. Converted to SI on validation.

ADR-002 D6: explicit unit object instead of suffix or SI-only float.
Avoids the 0.000183 vs 0.0000183 ambiguity.

Internally we keep BOTH the SI value (used by physics) and the
original unit (used by UI for round-trip display).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..foundation.units import convert_to_si, si_to


class Quantity(BaseModel):
    """A scalar with units.

    Stored canonically as SI in `value_si`. The original (`value`, `unit`)
    pair is preserved so the UI can round-trip back to the user's unit.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float = Field(..., description="Numerical value in given unit")
    unit: str = Field(..., description="Engineering unit, see foundation.units._TO_SI")
    value_si: float = Field(default=0.0, description="Auto-computed SI value")

    @model_validator(mode="after")
    def _to_si(self) -> Quantity:
        # frozen models: must use object.__setattr__
        object.__setattr__(self, "value_si", convert_to_si(self.value, self.unit))
        return self

    def to(self, unit: str) -> float:
        """Return the value converted to the requested unit."""
        return si_to(self.value_si, unit)

    def __repr__(self) -> str:
        return f"Quantity({self.value} {self.unit} = {self.value_si:g} SI)"
