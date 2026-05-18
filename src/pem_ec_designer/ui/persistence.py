"""QSettings persistence — keep stack / operating / economics across runs.

UX-VISION §9 spec:
    stack.{layer}                 → 7 component-IDs + 3 material-IDs
    op.{T_C, pH2_bar, pO2_bar, j_design_A_per_cm2}
    lcoh.{capex_eur_per_kw, electricity_eur_per_mwh}
    window.{w, h}
    ui.{show3d, onboardingSeen}

Layer rule: this module imports PySide6 (it MUST — QSettings lives there).
The serialise/deserialise functions stay simple dict<->QSettings, so they
can be exercised in tests by passing an `IniFormat` QSettings backed by
a tmp file.

QSettings semantics:
    - Missing keys → callers fall back to defaults silently (no raise).
    - Type-cast happens here: QSettings stores str on Ini-backed paths,
      so we round-trip floats / ints / bools explicitly.
"""

# ruff: noqa: I001
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from . import qt_env  # noqa: F401

from PySide6.QtCore import QSettings

from .stack_composer import StackSelection


# ── application-wide QSettings handle ─────────────────────────────────


ORG_NAME = "pem-ec-designer"
APP_NAME = "pem-ec-designer"


def default_settings() -> QSettings:
    """Per-user QSettings instance using the platform-native backend."""
    return QSettings(ORG_NAME, APP_NAME)


# ── helpers (type-cast around QSettings str-on-Ini) ───────────────────


def _get_str(s: QSettings, key: str) -> str | None:
    v = s.value(key, None)
    if v is None:
        return None
    return str(v)


def _get_float(s: QSettings, key: str, default: float) -> float:
    v = s.value(key, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _get_int(s: QSettings, key: str, default: int) -> int:
    v = s.value(key, default)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _get_bool(s: QSettings, key: str, default: bool) -> bool:
    v = s.value(key, default)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("1", "true", "yes")
    try:
        return bool(int(v))
    except (TypeError, ValueError):
        return default


# ── stack ─────────────────────────────────────────────────────────────


_STACK_FIELDS = (
    "membrane_id", "membrane_material_id",
    "anode_catalyst_material_id", "cathode_catalyst_material_id",
    "anode_cl_id", "cathode_cl_id",
    "anode_gdl_id", "cathode_gdl_id",
    "anode_bpp_id", "cathode_bpp_id",
)


def save_stack(settings: QSettings, sel: StackSelection) -> None:
    data = asdict(sel)
    for field in _STACK_FIELDS:
        val = data.get(field)
        settings.setValue(f"stack/{field}", "" if val is None else val)


def restore_stack(settings: QSettings) -> dict[str, str | None]:
    """Return a dict of stack-IDs (None where not stored). Caller validates."""
    out: dict[str, str | None] = {}
    for field in _STACK_FIELDS:
        v = _get_str(settings, f"stack/{field}")
        out[field] = v if v else None
    return out


# ── operating point ───────────────────────────────────────────────────


def save_operating_point(
    settings: QSettings,
    T_C: float,
    p_h2_bar: float,
    p_o2_bar: float,
    j_design_A_per_cm2: float,
) -> None:
    settings.setValue("op/T_C", float(T_C))
    settings.setValue("op/pH2_bar", float(p_h2_bar))
    settings.setValue("op/pO2_bar", float(p_o2_bar))
    settings.setValue("op/j_design_A_per_cm2", float(j_design_A_per_cm2))


def restore_operating_point(
    settings: QSettings,
    default_T_C: float = 80.0,
    default_p_h2_bar: float = 1.0,
    default_p_o2_bar: float = 1.0,
    default_j_A_per_cm2: float = 1.0,
) -> tuple[float, float, float, float]:
    return (
        _get_float(settings, "op/T_C", default_T_C),
        _get_float(settings, "op/pH2_bar", default_p_h2_bar),
        _get_float(settings, "op/pO2_bar", default_p_o2_bar),
        _get_float(settings, "op/j_design_A_per_cm2", default_j_A_per_cm2),
    )


# ── LCOH params ───────────────────────────────────────────────────────


def save_lcoh(settings: QSettings, capex_eur_per_kw: float, electricity_eur_per_mwh: float) -> None:
    settings.setValue("lcoh/capex_eur_per_kw", float(capex_eur_per_kw))
    settings.setValue("lcoh/electricity_eur_per_mwh", float(electricity_eur_per_mwh))


def restore_lcoh(
    settings: QSettings,
    default_capex: float = 1100.0,
    default_electricity: float = 50.0,
) -> tuple[float, float]:
    return (
        _get_float(settings, "lcoh/capex_eur_per_kw", default_capex),
        _get_float(settings, "lcoh/electricity_eur_per_mwh", default_electricity),
    )


# ── window + UI flags ────────────────────────────────────────────────


def save_window_size(settings: QSettings, w: int, h: int) -> None:
    settings.setValue("window/w", int(w))
    settings.setValue("window/h", int(h))


def restore_window_size(settings: QSettings, default_w: int = 1280, default_h: int = 900) -> tuple[int, int]:
    return (
        _get_int(settings, "window/w", default_w),
        _get_int(settings, "window/h", default_h),
    )


def save_ui_flags(settings: QSettings, show3d: bool, onboarding_seen: bool) -> None:
    settings.setValue("ui/show3d", bool(show3d))
    settings.setValue("ui/onboardingSeen", bool(onboarding_seen))


def restore_ui_flags(settings: QSettings) -> tuple[bool, bool]:
    return (
        _get_bool(settings, "ui/show3d", default=False),
        _get_bool(settings, "ui/onboardingSeen", default=False),
    )
