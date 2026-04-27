"""Material catalog and reference.

ADR-002 D3: Materials live separately in library/materials.json and are
referenced from components via MaterialRef. DRY: one material update
propagates to all components that use it.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .source import SourcedValue
from .units import Quantity


class MaterialRef(BaseModel):
    """A pointer to an entry in library/materials.json by ID."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ref: str = Field(..., min_length=1, description="Material ID, e.g. 'nafion-117'")


class Material(BaseModel):
    """Generic material spec.

    Subclasses can extend with category-specific fields (e.g.,
    catalyst loading is a Component property, not a Material property).
    """

    model_config = ConfigDict(extra="allow")  # extra: vendor-specific fields

    name: str
    vendor: str | None = None
    family: str | None = Field(
        default=None,
        description="e.g. 'PFSA membrane', 'Pt-group catalyst', 'Ti-felt'",
    )
    density: SourcedValue[Quantity] | None = None

    # Membrane-relevant
    sigma_S_per_m: SourcedValue[Quantity] | None = Field(
        default=None,
        description="Through-plane conductivity at 80 °C, fully hydrated",
    )
    ewt_g_per_eq: SourcedValue[Quantity] | None = Field(
        default=None,
        description="Equivalent weight (PFSA membranes)",
    )

    # Catalyst-relevant
    j0_anode: SourcedValue[Quantity] | None = Field(
        default=None,
        description="Exchange current density at reference state",
    )
    j0_cathode: SourcedValue[Quantity] | None = None
    tafel_slope: SourcedValue[Quantity] | None = None
