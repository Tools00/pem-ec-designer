"""Generic extrusion builder.

Any `Component` with a `footprint` and a `thickness` extrudes the same way.
Per-category modules (`membrane.py`, future `gdl.py`, ...) are thin wrappers
that exist for type-narrowing and category-specific decoration only.

Why generic: the schema base class `Component` already carries `footprint`
and `thickness`. Duplicating shape-dispatch logic per category would be DRY-
violating boilerplate. Category-specific *physics* belongs in the wrapper;
shape extrusion does not.
"""

from __future__ import annotations

from build123d import Box, Cylinder, Part

from ..schema import Component

_M_TO_MM = 1000.0


def build_extruded(component: Component) -> Part:
    """Extrude `component.footprint` by `component.thickness`.

    Returns a build123d Part in millimetres (build123d's native unit).
    Raises ValueError on missing footprint or unsupported shape.
    """
    if component.footprint is None:
        raise ValueError(
            f"{component.id!r}: no footprint; resolve at assembly level"
        )

    thickness_mm = component.thickness.value.value_si * _M_TO_MM
    fp = component.footprint

    if fp.shape == "circular":
        if fp.diameter is None:
            raise ValueError(f"{component.id!r}: circular footprint requires diameter")
        radius_mm = (fp.diameter.value_si * _M_TO_MM) / 2.0
        return Cylinder(radius=radius_mm, height=thickness_mm)

    if fp.shape in ("square", "rectangular"):
        if fp.width is None:
            raise ValueError(
                f"{component.id!r}: {fp.shape} footprint requires width"
            )
        width_mm = fp.width.value_si * _M_TO_MM
        height_mm = (fp.height.value_si * _M_TO_MM) if fp.height else width_mm
        return Box(length=width_mm, width=height_mm, height=thickness_mm)

    raise ValueError(f"{component.id!r}: unsupported footprint shape {fp.shape!r}")
