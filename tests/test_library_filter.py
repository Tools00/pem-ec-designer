"""Tests for assembly/library_filter — pure, no Qt."""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.assembly import library_filter as lf
from pem_ec_designer.materials import load_library


@pytest.fixture(scope="module")
def lib():
    return load_library(Path("library"))


def test_membranes_are_sorted_by_thickness(lib) -> None:
    ids = lf.membranes(lib)
    assert len(ids) == 5  # Nafion 115/117/211/212 + Aquivion E87
    thicknesses = [lib.components[i].thickness.value.value_si for i in ids]
    assert thicknesses == sorted(thicknesses)


def test_anode_and_cathode_cl_disjoint(lib) -> None:
    a = set(lf.anode_catalyst_layers(lib))
    c = set(lf.cathode_catalyst_layers(lib))
    assert a.isdisjoint(c)
    assert len(a) >= 1 and len(c) >= 1


def test_gas_diffusion_layers_sorted_by_thickness(lib) -> None:
    ids = lf.gas_diffusion_layers(lib)
    assert len(ids) >= 4  # Toray + SGL families
    thicknesses = [lib.components[i].thickness.value.value_si for i in ids]
    assert thicknesses == sorted(thicknesses)


def test_bipolar_plates_present(lib) -> None:
    ids = lf.bipolar_plates(lib)
    assert "bpp.poco.axf5q_5mm" in ids


def test_membrane_materials_excludes_bpp_substrate(lib) -> None:
    """poco-axf5q has σ = 6.8e4 S/m — must NOT appear as membrane material."""
    ids = lf.membrane_materials(lib)
    assert "nafion-1100" in ids
    assert "aquivion-870" in ids
    assert "poco-axf5q" not in ids
    assert "iro2-tio2-catalyst" not in ids


def test_anode_catalyst_materials_only_have_j0_anode(lib) -> None:
    ids = lf.anode_catalyst_materials(lib)
    assert "iro2-tio2-catalyst" in ids
    assert "pt-c-catalyst" not in ids
    for mid in ids:
        assert lib.materials[mid].j0_anode is not None


def test_cathode_catalyst_materials_only_have_j0_cathode(lib) -> None:
    ids = lf.cathode_catalyst_materials(lib)
    assert "pt-c-catalyst" in ids
    assert "iro2-tio2-catalyst" not in ids


def test_all_filters_return_sorted_deterministic_lists(lib) -> None:
    """Two calls must return identical order (deterministic for UI default)."""
    for fn in [
        lf.membranes, lf.anode_catalyst_layers, lf.cathode_catalyst_layers,
        lf.gas_diffusion_layers, lf.bipolar_plates,
        lf.membrane_materials, lf.anode_catalyst_materials, lf.cathode_catalyst_materials,
    ]:
        assert fn(lib) == fn(lib)


def test_filters_are_pure_no_qt_import() -> None:
    import pem_ec_designer.assembly.library_filter as mod
    src = Path(mod.__file__).read_text()
    assert "PySide6" not in src
    assert "PyQt" not in src
