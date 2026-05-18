"""Tests for assembly/source_collector — pure, no Qt."""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.assembly.source_collector import _bibtex_key, collect_source_keys
from pem_ec_designer.materials import load_library


@pytest.fixture(scope="module")
def lib():
    return load_library(Path("library"))


@pytest.mark.parametrize("raw,expected", [
    ("carmo2013ijhe.tab2", "carmo2013ijhe"),
    ("bernt2016jes.fig1a", "bernt2016jes"),
    ("kusoglu2017chemrev", "kusoglu2017chemrev"),
    ("chemours.datasheet.n117", "chemours.datasheet.n117"),
    ("entegris.datasheet.axf5q", "entegris.datasheet.axf5q"),
    ("toray.datasheet.tgph", "toray.datasheet.tgph"),
    ("bernt2016jes.eq3", "bernt2016jes"),
    ("schmidt2017ijhe.sec4", "schmidt2017ijhe"),
])
def test_bibtex_key_strips_locator_but_keeps_datasheet_id(raw, expected) -> None:
    assert _bibtex_key(raw) == expected


def test_collect_source_keys_from_default_stack(lib) -> None:
    """The hardcoded default stack must yield at least the 4 anchor papers."""
    components = [
        lib.components["membrane.nafion.212"],
        lib.components["gdl.sgl.39bb"],
        lib.components["bpp.poco.axf5q_5mm"],
        lib.components["anode_cl.bernt2016.optimal"],
        lib.components["cathode_cl.zhang2024.baseline"],
    ]
    materials = [
        lib.materials["nafion-1100"],
        lib.materials["iro2-tio2-catalyst"],
        lib.materials["pt-c-catalyst"],
        lib.materials["poco-axf5q"],
    ]
    keys = collect_source_keys(components, materials)
    # At least the validation-anchor papers should be present.
    assert "carmo2013ijhe" in keys
    assert "bernt2016jes" in keys
    assert "kusoglu2017chemrev" in keys
    # Datasheet keys must NOT be mistakenly stripped.
    assert "chemours.datasheet.n212" in keys or "entegris.datasheet.axf5q" in keys


def test_collect_source_keys_skips_none(lib) -> None:
    keys = collect_source_keys([None], [None])
    assert keys == set()


def test_collect_source_keys_no_qt_import() -> None:
    import pem_ec_designer.assembly.source_collector as mod
    assert "PySide6" not in Path(mod.__file__).read_text()
