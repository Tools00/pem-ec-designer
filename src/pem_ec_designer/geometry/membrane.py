"""Membrane geometry generator.

Builds a parametric solid from a `Membrane` spec using its `footprint` (2D
shape) extruded by `thickness`. SI values (meters) come from the schema's
`value_si` and are converted to mm for build123d (its native unit).
"""

from __future__ import annotations

from build123d import Box, Cylinder, Part

from ..schema import Membrane

_M_TO_MM = 1000.0


def build_membrane(spec: Membrane) -> Part:
    """Return a build123d Part for the given membrane spec.

    Requires `spec.footprint` to be set. Raises ValueError otherwise — stack-
    default footprints are resolved one layer up (assembly), not here.
    """
    if spec.footprint is None:
        raise ValueError(
            f"Membrane {spec.id!r} has no footprint; resolve at assembly level"
        )

    thickness_mm = spec.thickness.value.value_si * _M_TO_MM
    fp = spec.footprint

    if fp.shape == "circular":
        if fp.diameter is None:
            raise ValueError(f"{spec.id!r}: circular footprint requires diameter")
        radius_mm = (fp.diameter.value_si * _M_TO_MM) / 2.0
        return Cylinder(radius=radius_mm, height=thickness_mm)

    if fp.shape in ("square", "rectangular"):
        if fp.width is None:
            raise ValueError(f"{spec.id!r}: {fp.shape} footprint requires width")
        width_mm = fp.width.value_si * _M_TO_MM
        height_mm = (fp.height.value_si * _M_TO_MM) if fp.height else width_mm
        return Box(length=width_mm, width=height_mm, height=thickness_mm)

    raise ValueError(f"{spec.id!r}: unsupported footprint shape {fp.shape!r}")
