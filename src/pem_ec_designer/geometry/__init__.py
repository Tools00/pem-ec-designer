"""Parametric CAD generators (build123d, headless — no Qt).

`build_extruded` is the generic workhorse; per-category wrappers exist for
type narrowing.
"""

from .extruded import build_extruded
from .membrane import build_membrane

__all__ = ["build_extruded", "build_membrane"]
