"""Geometry smoke test: load a real membrane spec, build a Part, export STEP."""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.geometry import build_membrane
from pem_ec_designer.materials import load_library
from pem_ec_designer.schema import Membrane


@pytest.fixture(scope="module")
def nafion_117() -> Membrane:
    lib = load_library(Path(__file__).resolve().parents[1] / "library")
    spec = lib.components["membrane.nafion.117"]
    assert isinstance(spec, Membrane)
    return spec


def test_build_membrane_has_volume(nafion_117: Membrane) -> None:
    part = build_membrane(nafion_117)
    # 50 mm dia, 0.183 mm thick: V = pi * 25^2 * 0.183 ~= 359 mm^3
    assert part.volume == pytest.approx(359.2, rel=0.01)


def test_membrane_step_export(nafion_117: Membrane, tmp_path: Path) -> None:
    from build123d import export_step

    part = build_membrane(nafion_117)
    out = tmp_path / "nafion_117.step"
    export_step(part, str(out))
    assert out.exists()
    assert out.stat().st_size > 0
    # STEP files start with "ISO-10303"
    assert out.read_bytes()[:9] == b"ISO-10303"
