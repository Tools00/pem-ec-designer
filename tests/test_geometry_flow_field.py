"""Flow-field generator: straight_parallel pattern + error paths.

Synthetic specs (no library/BibTeX involvement) — geometry is independent
of source-tracking. Volume is the gold check: V_plate - n * V_channel.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.geometry import build_flow_field
from pem_ec_designer.schema import FlowField, Footprint
from pem_ec_designer.schema.material import MaterialRef
from pem_ec_designer.schema.source import SourcedValue
from pem_ec_designer.schema.units import Quantity


def _q(v: float, u: str) -> Quantity:
    return Quantity(value=v, unit=u)


def _sv(v: float, u: str) -> SourcedValue[Quantity]:
    return SourcedValue[Quantity](
        value=_q(v, u), source="test.synthetic", confidence="estimate"
    )


def _ff(
    *,
    pattern: str = "straight_parallel",
    width_mm: float = 50.0,
    height_mm: float = 30.0,
    thickness_mm: float = 3.0,
    cw_mm: float = 1.0,
    cd_mm: float = 1.0,
    pitch_mm: float = 2.0,
) -> FlowField:
    return FlowField(
        id="flowfield.test.synthetic",
        name="Synthetic flow-field",
        material=MaterialRef(ref="nafion-1100"),
        thickness=_sv(thickness_mm, "mm"),
        footprint=Footprint(
            shape="rectangular",
            width=_q(width_mm, "mm"),
            height=_q(height_mm, "mm"),
        ),
        pattern=pattern,  # type: ignore[arg-type]
        channel_width=_sv(cw_mm, "mm"),
        channel_depth=_sv(cd_mm, "mm"),
        channel_pitch=_sv(pitch_mm, "mm"),
    )


def test_straight_parallel_volume_matches_subtraction() -> None:
    # 50 x 30 x 3 plate = 4500 mm^3
    # channels: width 1, depth 1, pitch 2 → n = floor((30-1)/2)+1 = 15
    # each channel volume = 50 * 1 * 1 = 50 mm^3 → 15 * 50 = 750 mm^3
    # expected: 4500 - 750 = 3750
    part = build_flow_field(_ff())
    assert part.volume == pytest.approx(3750.0, rel=1e-4)


def test_serpentine_not_implemented_yet() -> None:
    with pytest.raises(NotImplementedError, match="serpentine"):
        build_flow_field(_ff(pattern="serpentine"))


def test_channel_overlap_rejected() -> None:
    with pytest.raises(ValueError, match="overlap"):
        build_flow_field(_ff(cw_mm=2.0, pitch_mm=1.5))


def test_channel_too_deep_rejected() -> None:
    with pytest.raises(ValueError, match="cut through"):
        build_flow_field(_ff(cd_mm=3.0, thickness_mm=3.0))


def test_circular_footprint_rejected() -> None:
    spec = _ff()
    spec = spec.model_copy(
        update={"footprint": Footprint(shape="circular", diameter=_q(50.0, "mm"))}
    )
    with pytest.raises(ValueError, match="rectangular footprint"):
        build_flow_field(spec)


def test_step_export_smoke(tmp_path: Path) -> None:
    from build123d import export_step

    part = build_flow_field(_ff())
    out = tmp_path / "ff.step"
    export_step(part, str(out))
    assert out.read_bytes()[:9] == b"ISO-10303"
