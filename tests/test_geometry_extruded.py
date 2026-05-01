"""Generic extruder: rectangular branch + error paths.

The Membrane case is covered by test_geometry_membrane.py (real spec from
library, circular footprint). Here we exercise the rectangular footprint
and validation errors using in-memory synthetic specs — no library/BibTeX
involvement, since shape extrusion is independent of source-tracking.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pem_ec_designer.geometry import build_extruded
from pem_ec_designer.schema import (
    Footprint,
    GasDiffusionLayer,
    Membrane,
)
from pem_ec_designer.schema.material import MaterialRef
from pem_ec_designer.schema.source import SourcedValue
from pem_ec_designer.schema.units import Quantity


def _q(value: float, unit: str) -> Quantity:
    return Quantity(value=value, unit=unit)


def _sv(value: float, unit: str, source: str = "test.synthetic") -> SourcedValue[Quantity]:
    return SourcedValue[Quantity](
        value=_q(value, unit), source=source, confidence="estimate"
    )


def _gdl(footprint: Footprint, thickness_um: float = 200.0) -> GasDiffusionLayer:
    return GasDiffusionLayer(
        id="gdl.test.synthetic",
        name="Synthetic GDL for shape test",
        material=MaterialRef(ref="nafion-1100"),  # ref not validated here
        thickness=_sv(thickness_um, "um"),
        footprint=footprint,
    )


def test_rectangular_footprint_volume() -> None:
    fp = Footprint(
        shape="rectangular",
        width=_q(50.0, "mm"),
        height=_q(30.0, "mm"),
    )
    part = build_extruded(_gdl(fp, thickness_um=200.0))
    # 50 * 30 * 0.2 mm = 300 mm^3
    assert part.volume == pytest.approx(300.0, rel=1e-6)


def test_square_footprint_uses_width_when_height_missing() -> None:
    fp = Footprint(shape="square", width=_q(40.0, "mm"))
    part = build_extruded(_gdl(fp, thickness_um=200.0))
    # 40 * 40 * 0.2 = 320 mm^3
    assert part.volume == pytest.approx(320.0, rel=1e-6)


def test_missing_footprint_raises() -> None:
    spec = GasDiffusionLayer(
        id="gdl.test.no.footprint",
        name="No footprint",
        material=MaterialRef(ref="nafion-1100"),
        thickness=_sv(200.0, "um"),
        footprint=None,
    )
    with pytest.raises(ValueError, match="no footprint"):
        build_extruded(spec)


def test_circular_without_diameter_raises() -> None:
    fp = Footprint(shape="circular")  # no diameter
    with pytest.raises(ValueError, match="diameter"):
        build_extruded(_gdl(fp))


def test_membrane_still_works_via_generic_path(tmp_path: Path) -> None:
    """Round-trip: a real Membrane goes through build_extruded unchanged."""
    from pem_ec_designer.materials import load_library

    lib = load_library(Path(__file__).resolve().parents[1] / "library")
    spec = lib.components["membrane.nafion.115"]
    assert isinstance(spec, Membrane)
    part = build_extruded(spec)
    # 50 mm dia, 0.127 mm thick: pi * 25^2 * 0.127
    expected = math.pi * 25.0**2 * 0.127
    assert part.volume == pytest.approx(expected, rel=0.01)
