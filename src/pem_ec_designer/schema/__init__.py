"""Pydantic schema for component specifications.

Per ADR-002:
- D2: Pydantic v2 + auto-gen JSON Schema
- D6: Quantity = explicit {value, unit} object, converted to SI on load

Submodules:
- units: Quantity model
- source: SourcedValue, Source-ID validation
- material: Material, MaterialRef
- component: Component base class + per-category subclasses
"""

from .component import (
    AnodeCatalystLayer,
    BipolarPlate,
    CathodeCatalystLayer,
    Component,
    Endplate,
    FlowField,
    Gasket,
    GasDiffusionLayer,
    Membrane,
)
from .material import Material, MaterialRef
from .source import SourcedValue, SourceId
from .units import Quantity

__all__ = [
    "Quantity",
    "SourcedValue",
    "SourceId",
    "Material",
    "MaterialRef",
    "Component",
    "Membrane",
    "AnodeCatalystLayer",
    "CathodeCatalystLayer",
    "GasDiffusionLayer",
    "BipolarPlate",
    "FlowField",
    "Endplate",
    "Gasket",
]
