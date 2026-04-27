"""End-to-end library load test.

Loads library/ as committed; expects 5 membranes, 2 materials, all
sources resolve in sources.bib. This is the strict-quellen-gate.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pem_ec_designer.materials import LibraryLoadError, load_library


@pytest.fixture(scope="module")
def lib_dir() -> Path:
    root = Path(__file__).resolve().parents[1] / "library"
    assert root.is_dir(), f"library dir missing: {root}"
    return root


def test_library_loads(lib_dir: Path) -> None:
    lib = load_library(lib_dir)
    assert len(lib.materials) >= 2
    assert len(lib.components) >= 5
    assert len(lib.sources) >= 8


def test_membrane_specs_loaded(lib_dir: Path) -> None:
    lib = load_library(lib_dir)
    expected = {
        "membrane.nafion.115",
        "membrane.nafion.117",
        "membrane.nafion.211",
        "membrane.nafion.212",
        "membrane.aquivion.e87",
    }
    assert expected.issubset(lib.components.keys())


def test_material_resolves(lib_dir: Path) -> None:
    lib = load_library(lib_dir)
    m = lib.get_component("membrane.nafion.117")
    mat = lib.get_material(m.material.ref)
    assert mat.name.startswith("Nafion")


def test_si_value_correct(lib_dir: Path) -> None:
    lib = load_library(lib_dir)
    m117 = lib.get_component("membrane.nafion.117")
    # 183 µm should round-trip to 1.83e-4 m
    assert math.isclose(m117.thickness.value.value_si, 1.83e-4, rel_tol=1e-12)


def test_strict_sources_break_on_missing(tmp_path: Path) -> None:
    """A component citing a missing source must fail to load."""
    bad = tmp_path / "library"
    (bad / "components").mkdir(parents=True)
    (bad / "sources.bib").write_text("@misc{realkey, title={x}}\n")
    (bad / "materials.json").write_text("{}")
    (bad / "components" / "membrane.json").write_text(
        """{
          "membrane.x.1": {
            "category": "membrane",
            "name": "x",
            "material": {"ref": "nonexistent"},
            "thickness": {
              "value": {"value": 100, "unit": "um"},
              "source": "ghostkey.tab1"
            }
          }
        }"""
    )
    with pytest.raises(LibraryLoadError, match="Strict-Quellen"):
        load_library(bad)
