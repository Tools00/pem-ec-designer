"""Tests for ui/source_tooltip — pure formatting, no Qt needed."""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.materials import load_library
from pem_ec_designer.ui.source_tooltip import (
    format_material_kinetics_tooltip,
    format_source_tooltip,
    format_thickness_tooltip,
)


@pytest.fixture(scope="module")
def lib():
    return load_library(Path("library"))


def test_format_source_tooltip_includes_bibkey(lib) -> None:
    comp = lib.components["membrane.nafion.212"]
    out = format_source_tooltip(comp.thickness, label="Thickness · Nafion 212")
    assert "Thickness · Nafion 212" in out
    assert "<code>" in out
    assert comp.thickness.source in out
    assert "Confidence" in out


def test_format_source_tooltip_empty_for_none() -> None:
    assert format_source_tooltip(None) == ""


def test_format_thickness_tooltip_pulls_from_component(lib) -> None:
    comp = lib.components["membrane.nafion.117"]
    out = format_thickness_tooltip(comp)
    assert "membrane.nafion.117" in out
    assert comp.thickness.source in out


def test_format_thickness_tooltip_safe_for_none() -> None:
    assert format_thickness_tooltip(None) == ""


def test_material_kinetics_tooltip_anode(lib) -> None:
    mat = lib.materials["iro2-tio2-catalyst"]
    out = format_material_kinetics_tooltip(mat, role="anode")
    assert mat.name in out
    assert "j₀,anode" in out
    assert "α,anode" in out
    assert mat.j0_anode.source in out


def test_material_kinetics_tooltip_cathode(lib) -> None:
    mat = lib.materials["pt-c-catalyst"]
    out = format_material_kinetics_tooltip(mat, role="cathode")
    assert "j₀,cathode" in out
    assert mat.j0_cathode.source in out


def test_material_kinetics_tooltip_membrane_ionomer_has_sigma(lib) -> None:
    mat = lib.materials["nafion-1100"]
    out = format_material_kinetics_tooltip(mat, role="anode")
    # No kinetic on Nafion → still shows σ
    assert "σ" in out
    assert mat.sigma_S_per_m.source in out


def test_tooltip_helper_has_no_qt_imports() -> None:
    import pem_ec_designer.ui.source_tooltip as mod
    src = Path(mod.__file__).read_text()
    assert "PySide6" not in src
    assert "PyQt" not in src
