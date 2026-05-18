"""Tests for ui/persistence — QSettings roundtrips.

Uses IniFormat + tmp_path so each test gets an isolated settings file —
no interference with the user's real platform-native settings.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.ui import qt_env  # noqa: F401

from PySide6.QtCore import QSettings  # noqa: E402

from pem_ec_designer.ui.persistence import (  # noqa: E402
    restore_lcoh,
    restore_operating_point,
    restore_stack,
    restore_ui_flags,
    restore_window_size,
    save_lcoh,
    save_operating_point,
    save_stack,
    save_ui_flags,
    save_window_size,
)
from pem_ec_designer.ui.stack_composer import StackSelection  # noqa: E402


def _ini(tmp_path: Path) -> QSettings:
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


# ── stack ─────────────────────────────────────────────────────────────


def test_stack_roundtrip(tmp_path) -> None:
    sel = StackSelection(
        membrane_id="membrane.nafion.117",
        membrane_material_id="nafion-1100",
        anode_catalyst_material_id="iro2-tio2-catalyst",
        cathode_catalyst_material_id="pt-c-catalyst",
        anode_cl_id="anode_cl.bernt2016.optimal",
        cathode_cl_id="cathode_cl.zhang2024.baseline",
        anode_gdl_id="gdl.toray.tgph060",
        cathode_gdl_id="gdl.toray.tgph060",
        anode_bpp_id="bpp.poco.axf5q_5mm",
        cathode_bpp_id="bpp.poco.axf5q_5mm",
    )
    s = _ini(tmp_path)
    save_stack(s, sel)
    s.sync()
    restored = restore_stack(_ini(tmp_path))
    assert restored["membrane_id"] == "membrane.nafion.117"
    assert restored["anode_gdl_id"] == "gdl.toray.tgph060"


def test_restore_stack_returns_none_for_empty_keys(tmp_path) -> None:
    s = _ini(tmp_path)
    restored = restore_stack(s)
    for v in restored.values():
        assert v is None


def test_stack_with_partial_none_fields(tmp_path) -> None:
    sel = StackSelection(
        membrane_id="membrane.nafion.212",
        membrane_material_id="nafion-1100",
        anode_catalyst_material_id="iro2-tio2-catalyst",
        cathode_catalyst_material_id="pt-c-catalyst",
        anode_cl_id=None,
        cathode_cl_id=None,
        anode_gdl_id=None, cathode_gdl_id=None,
        anode_bpp_id=None, cathode_bpp_id=None,
    )
    s = _ini(tmp_path)
    save_stack(s, sel)
    s.sync()
    restored = restore_stack(_ini(tmp_path))
    assert restored["membrane_id"] == "membrane.nafion.212"
    assert restored["anode_cl_id"] is None
    assert restored["anode_gdl_id"] is None


# ── operating point ───────────────────────────────────────────────────


def test_operating_point_roundtrip(tmp_path) -> None:
    s = _ini(tmp_path)
    save_operating_point(s, T_C=85.0, p_h2_bar=4.0, p_o2_bar=2.0, j_design_A_per_cm2=1.5)
    s.sync()
    T_C, ph2, po2, j = restore_operating_point(_ini(tmp_path))
    assert T_C == pytest.approx(85.0)
    assert ph2 == pytest.approx(4.0)
    assert po2 == pytest.approx(2.0)
    assert j == pytest.approx(1.5)


def test_operating_point_defaults_when_unset(tmp_path) -> None:
    T_C, ph2, po2, j = restore_operating_point(_ini(tmp_path))
    assert T_C == 80.0 and ph2 == 1.0 and po2 == 1.0 and j == 1.0


def test_operating_point_corrupt_value_falls_back_to_default(tmp_path) -> None:
    s = _ini(tmp_path)
    s.setValue("op/T_C", "not-a-number")
    s.sync()
    T_C, _, _, _ = restore_operating_point(_ini(tmp_path), default_T_C=70.0)
    assert T_C == 70.0


# ── LCOH ──────────────────────────────────────────────────────────────


def test_lcoh_roundtrip(tmp_path) -> None:
    s = _ini(tmp_path)
    save_lcoh(s, capex_eur_per_kw=1700.0, electricity_eur_per_mwh=75.0)
    s.sync()
    capex, elec = restore_lcoh(_ini(tmp_path))
    assert capex == pytest.approx(1700.0)
    assert elec == pytest.approx(75.0)


def test_lcoh_defaults(tmp_path) -> None:
    capex, elec = restore_lcoh(_ini(tmp_path))
    assert capex == 1100.0
    assert elec == 50.0


# ── window + UI flags ────────────────────────────────────────────────


def test_window_size_roundtrip(tmp_path) -> None:
    s = _ini(tmp_path)
    save_window_size(s, 1600, 1000)
    s.sync()
    assert restore_window_size(_ini(tmp_path)) == (1600, 1000)


def test_ui_flags_roundtrip(tmp_path) -> None:
    s = _ini(tmp_path)
    save_ui_flags(s, show3d=True, onboarding_seen=True)
    s.sync()
    assert restore_ui_flags(_ini(tmp_path)) == (True, True)


def test_ui_flags_string_storage_roundtrip(tmp_path) -> None:
    """Some Ini backends serialise booleans as 'true'/'false' strings."""
    s = _ini(tmp_path)
    s.setValue("ui/show3d", "true")
    s.setValue("ui/onboardingSeen", "false")
    s.sync()
    assert restore_ui_flags(_ini(tmp_path)) == (True, False)
