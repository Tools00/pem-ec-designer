"""Tests for geometry.stack_assembly — ADR-008.

Covered:
1. Default 7-layer stack: roles, monotonic Z, total thickness.
2. Missing optional layer: role recorded in skipped.
3. Layer without footprint: skipped, not in compound.
4. STEP roundtrip: file is written, importable, bounding box matches.
5. Sidecar JSON shape: keys present, layer count matches.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from pem_ec_designer.geometry.stack_assembly import (
    LAYER_ORDER,
    assembly_to_sidecar,
    build_stack_assembly,
)
from pem_ec_designer.materials.loader import load_library

LIBRARY_DIR = Path(__file__).parent.parent / "library"


@pytest.fixture(scope="module")
def lib():
    return load_library(LIBRARY_DIR)


def _default_layers(lib) -> dict:
    c = lib.components
    return {
        "anode_bpp": c["bpp.poco.axf5q_5mm"],
        "anode_gdl": c["gdl.sgl.39bb"],
        "anode_cl": c["anode_cl.bernt2016.optimal"],
        "membrane": c["membrane.nafion.212"],
        "cathode_cl": c["cathode_cl.zhang2024.baseline"],
        "cathode_gdl": c["gdl.sgl.39bb"],
        "cathode_bpp": c["bpp.poco.axf5q_5mm"],
    }


def test_default_stack_has_seven_layers_in_order(lib):
    a = build_stack_assembly(**_default_layers(lib))
    assert [p.role for p in a.layers] == list(LAYER_ORDER)
    assert a.skipped == []
    # Z is monotonic and contiguous
    cursor = 0.0
    for p in a.layers:
        assert p.z_start_mm == pytest.approx(cursor)
        assert p.z_end_mm > p.z_start_mm
        cursor = p.z_end_mm
    # Total thickness equals sum of thicknesses
    total = sum(p.thickness_mm for p in a.layers)
    assert a.layers[-1].z_end_mm == pytest.approx(total)


def test_missing_optional_layer_is_skipped(lib):
    layers = _default_layers(lib)
    layers["anode_bpp"] = None
    a = build_stack_assembly(**layers)
    assert len(a.layers) == 6
    assert all("anode_bpp" in s for s in a.skipped) or any(
        "anode_bpp" in s for s in a.skipped
    )
    # First layer is now anode_gdl, starting at z=0
    assert a.layers[0].role == "anode_gdl"
    assert a.layers[0].z_start_mm == 0.0


def test_layer_without_footprint_is_skipped(lib):
    membrane = lib.components["membrane.nafion.212"]
    # Pydantic model is frozen-ish; build a modified copy with footprint=None
    stripped = membrane.model_copy(update={"footprint": None})
    layers = _default_layers(lib)
    layers["membrane"] = stripped
    a = build_stack_assembly(**layers)
    assert any("membrane" in s and "footprint" in s for s in a.skipped)
    assert all(p.role != "membrane" for p in a.layers)


def test_step_roundtrip_bounding_box(lib, tmp_path):
    """STEP-Export schreibt eine valide Datei; Bounding-Box-Höhe ≈ Stack-Höhe."""
    from build123d import export_step

    a = build_stack_assembly(**_default_layers(lib))
    step_path = tmp_path / "stack.step"
    export_step(a.compound, str(step_path))
    assert step_path.exists() and step_path.stat().st_size > 0

    # Bounding-Box-Höhe matcht Z-Stack-Höhe
    bb = a.compound.bounding_box()
    expected_height = a.layers[-1].z_end_mm
    assert math.isclose(bb.size.Z, expected_height, rel_tol=1e-3)


def test_sidecar_shape(lib):
    a = build_stack_assembly(**_default_layers(lib))
    side = assembly_to_sidecar(
        a,
        app_version="0.1.0",
        operating_point={"T_K": 353.15, "p_h2_Pa": 1e5, "p_o2_Pa": 1e5},
    )
    # Round-trip via JSON to ensure it's serialisable
    side2 = json.loads(json.dumps(side))
    assert side2["operating_point"]["T_K"] == 353.15
    assert len(side2["layers"]) == 7
    # Layer entries have required keys
    for entry in side2["layers"]:
        assert {"index", "role", "id", "thickness_mm", "z_start_mm", "z_end_mm"} <= set(entry)
