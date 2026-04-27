"""Component specifications — base + per-category subclasses.

ADR-002 D5: hierarchical IDs (e.g., 'membrane.nafion.117').
ADR-002 D3: components reference materials, do not embed.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .material import MaterialRef
from .source import SourcedValue
from .units import Quantity


# 2D footprint shape — used for parametric build123d generation later
class Footprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shape: Literal["circular", "square", "rectangular"]
    diameter: Quantity | None = Field(default=None, description="circular only")
    width: Quantity | None = Field(default=None, description="rectangular/square")
    height: Quantity | None = Field(default=None, description="rectangular only")
    corner_radius: Quantity | None = Field(default=None, description="optional fillet")


_HIERARCHICAL_ID = r"^[a-z0-9]+(\.[a-z0-9]+){1,3}$"


class Component(BaseModel):
    """Base component spec. All categories extend this."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        pattern=_HIERARCHICAL_ID,
        description="Hierarchical slug, e.g. 'membrane.nafion.117'",
    )
    category: str
    name: str = Field(..., description="Human-readable EN")
    name_de: str | None = Field(default=None, description="Optional DE label for UI")

    material: MaterialRef
    thickness: SourcedValue[Quantity]
    cost: SourcedValue[Quantity] | None = Field(
        default=None,
        description="Cost per unit (cell, pcs, kg, m^2). Null = unknown.",
    )
    footprint: Footprint | None = Field(
        default=None,
        description="2D footprint for build123d generation. Null = stack-default.",
    )

    @field_validator("category")
    @classmethod
    def _category_matches_id(cls, v: str, info: object) -> str:
        # info.data is the partially-built dict; in pydantic v2 use ValidationInfo
        return v


# ─── Per-category subclasses ────────────────────────────────────────


class Membrane(Component):
    category: Literal["membrane"] = "membrane"
    sigma_S_per_m: SourcedValue[Quantity] | None = Field(  # noqa: N815  (S = Siemens, physics symbol)
        default=None,
        description="Override material conductivity for this specific membrane",
    )


class AnodeCatalystLayer(Component):
    category: Literal["anode_cl"] = "anode_cl"
    catalyst_loading: SourcedValue[Quantity]  # mg/cm² typically


class CathodeCatalystLayer(Component):
    category: Literal["cathode_cl"] = "cathode_cl"
    catalyst_loading: SourcedValue[Quantity]


class GasDiffusionLayer(Component):
    category: Literal["gdl"] = "gdl"
    porosity: SourcedValue[Quantity] | None = None
    permeability: SourcedValue[Quantity] | None = None


class BipolarPlate(Component):
    category: Literal["bpp"] = "bpp"
    coating: str | None = None


class FlowField(Component):
    category: Literal["flow_field"] = "flow_field"
    pattern: Literal["straight_parallel", "serpentine", "interdigitated", "mesh", "pin_fin"]
    channel_width: SourcedValue[Quantity] | None = None
    channel_depth: SourcedValue[Quantity] | None = None
    channel_pitch: SourcedValue[Quantity] | None = None


class Endplate(Component):
    category: Literal["endplate"] = "endplate"


class Gasket(Component):
    category: Literal["gasket"] = "gasket"
