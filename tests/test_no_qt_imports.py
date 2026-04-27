"""Smoke test: physics/foundation/schema layers must NOT import Qt.

Per ADR-001 §3.1: layer-trennung non-negotiable. Importing
src.pem_ec_designer.physics with Qt unavailable must succeed.
"""

from __future__ import annotations

import importlib
import sys

import pytest


@pytest.mark.no_qt
@pytest.mark.parametrize(
    "module",
    [
        "pem_ec_designer",
        "pem_ec_designer.foundation",
        "pem_ec_designer.foundation.constants",
        "pem_ec_designer.foundation.units",
        "pem_ec_designer.schema",
        "pem_ec_designer.schema.units",
        "pem_ec_designer.schema.source",
        "pem_ec_designer.schema.material",
        "pem_ec_designer.schema.component",
        "pem_ec_designer.materials",
        "pem_ec_designer.materials.loader",
        "pem_ec_designer.physics",
        "pem_ec_designer.assembly",
    ],
)
def test_imports_without_qt(module: str) -> None:
    """Each non-UI module loads even when PySide6 is missing."""
    importlib.import_module(module)


def test_no_qt_in_physics_layer() -> None:
    """Verify no submodule of pem_ec_designer.physics or schema
    imports a Qt module."""
    forbidden = {"PySide6", "PyQt6", "PyQt5", "pyvistaqt"}
    # Need to import the package first
    importlib.import_module("pem_ec_designer.physics")
    importlib.import_module("pem_ec_designer.schema")
    for name in list(sys.modules):
        if name.startswith("pem_ec_designer.physics") or name.startswith(
            "pem_ec_designer.schema"
        ):
            mod = sys.modules[name]
            for forbidden_mod in forbidden:
                assert forbidden_mod not in (
                    getattr(mod, "__dict__", {}).keys()
                ), f"{name} unexpectedly imports {forbidden_mod}"
