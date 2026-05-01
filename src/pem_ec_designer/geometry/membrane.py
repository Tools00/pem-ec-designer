"""Membrane geometry — thin wrapper around the generic extrusion builder.

Exists for type-narrowing (callers get `Membrane` not `Component`) and as
the natural home for any future membrane-specific CAD decoration (e.g.,
edge sealing, reinforcement layers).
"""

from __future__ import annotations

from build123d import Part

from ..schema import Membrane
from .extruded import build_extruded


def build_membrane(spec: Membrane) -> Part:
    """Return a build123d Part for the given membrane spec."""
    return build_extruded(spec)
