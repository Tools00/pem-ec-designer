"""ValidationBadge — header indicator for V(1 A/cm²) vs. literature anchor.

UX-VISION §6.4. Three-state badge:
    ✓ green   if  |V_model − 1.60 V| / 1.60 V < 5 %
    ⚠ yellow  if  5 % – 15 %
    ✗ red     if  > 15 %

Anchor: Bernt 2016 (JES, DOI 10.1149/2.0731609jes) reports V(1 A/cm²) =
1.50 – 1.70 V for a typical PEM-EC cell at 80 °C. Midpoint 1.60 V is the
v1.0 reference; broader anchors (Carmo 2013 @ 2 A/cm²) are documented in
UX-VISION but not folded into the badge yet.

The classification logic lives as a pure function `classify_deviation`
so it stays testable without Qt.
"""

# ruff: noqa: I001
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from . import qt_env  # noqa: F401

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QMessageBox, QWidget

BadgeState = Literal["ok", "warn", "fail"]

# Bernt-2016 anchor at 1 A/cm² (UX-VISION §6.4)
ANCHOR_V: float = 1.60
ANCHOR_BAND_LOW: float = 1.50
ANCHOR_BAND_HIGH: float = 1.70
ANCHOR_BIBKEY: str = "bernt2016jes"
ANCHOR_J_A_PER_CM2: float = 1.0

WARN_THRESHOLD: float = 0.05  # 5 %
FAIL_THRESHOLD: float = 0.15  # 15 %


@dataclass(frozen=True)
class ValidationResult:
    """Pure-data result of one validation evaluation."""

    state: BadgeState
    v_model: float
    deviation_fraction: float
    deviation_percent: float

    @property
    def symbol(self) -> str:
        return {"ok": "✓", "warn": "⚠", "fail": "✗"}[self.state]


def classify_deviation(v_model: float) -> ValidationResult:
    """Classify V_model against the Bernt-2016 anchor (V=1.60 V @ 1 A/cm²).

    Args:
        v_model: cell voltage at 1 A/cm² in volts.

    Returns:
        ValidationResult with state + deviation. NaN/invalid V_model → "fail".
    """
    if v_model <= 0 or v_model != v_model:  # NaN check
        return ValidationResult(state="fail", v_model=v_model, deviation_fraction=1.0,
                                deviation_percent=100.0)
    dev_frac = abs(v_model - ANCHOR_V) / ANCHOR_V
    if dev_frac < WARN_THRESHOLD:
        state: BadgeState = "ok"
    elif dev_frac < FAIL_THRESHOLD:
        state = "warn"
    else:
        state = "fail"
    return ValidationResult(
        state=state,
        v_model=v_model,
        deviation_fraction=dev_frac,
        deviation_percent=dev_frac * 100.0,
    )


# Colors from UX-VISION §7
_COLORS: dict[BadgeState, str] = {
    "ok":   "#2E7D32",  # green
    "warn": "#ED6C02",  # orange
    "fail": "#C62828",  # red
}


class ValidationBadge(QLabel):
    """Click-to-explain badge. Updates state via `set_voltage(v_model)`."""

    clicked = Signal()  # emitted on mouse release

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(140)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText("—  no model")
        self.setStyleSheet(
            "QLabel { padding: 4px 10px; border-radius: 4px; "
            "background: #EEE; color: #444; font-weight: bold; }"
        )
        self._last: ValidationResult | None = None
        self.clicked.connect(self._show_explanation)

    # Qt: turn mouse release into our `clicked` Signal.
    def mouseReleaseEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(ev)

    def set_voltage(self, v_model: float) -> None:
        result = classify_deviation(v_model)
        self._last = result
        color = _COLORS[result.state]
        self.setText(
            f"{result.symbol}  V(1 A/cm²) = {v_model:.2f} V "
            f"(Δ {result.deviation_percent:.1f} %)"
        )
        self.setStyleSheet(
            f"QLabel {{ padding: 4px 10px; border-radius: 4px; "
            f"background: {color}; color: white; font-weight: bold; }}"
        )
        self.setToolTip(
            f"Validation anchor: Bernt 2016 @ 1 A/cm² → V = {ANCHOR_V:.2f} V "
            f"(band {ANCHOR_BAND_LOW:.2f}–{ANCHOR_BAND_HIGH:.2f} V)<br>"
            f"Model: V = {v_model:.3f} V<br>"
            f"Deviation: {result.deviation_percent:.2f} %<br>"
            f"Source: <code>{ANCHOR_BIBKEY}</code>"
        )

    def _show_explanation(self) -> None:
        if self._last is None:
            return
        r = self._last
        msg = QMessageBox(self)
        msg.setIcon({
            "ok": QMessageBox.Icon.Information,
            "warn": QMessageBox.Icon.Warning,
            "fail": QMessageBox.Icon.Critical,
        }[r.state])
        msg.setWindowTitle("Model validation vs. literature anchor")
        msg.setText(
            f"<b>{r.symbol}  Deviation {r.deviation_percent:.2f} %</b><br><br>"
            f"Model:  V({ANCHOR_J_A_PER_CM2:.0f} A/cm²) = {r.v_model:.3f} V<br>"
            f"Anchor: V = {ANCHOR_V:.2f} V  (band {ANCHOR_BAND_LOW:.2f}–{ANCHOR_BAND_HIGH:.2f} V)<br>"
            f"Source: <code>{ANCHOR_BIBKEY}</code>  "
            f"(DOI 10.1149/2.0731609jes)<br><br>"
            f"Thresholds (UX-VISION §6.4): "
            f"&lt; {WARN_THRESHOLD * 100:.0f} % ✓ · "
            f"{WARN_THRESHOLD * 100:.0f}–{FAIL_THRESHOLD * 100:.0f} % ⚠ · "
            f"&gt; {FAIL_THRESHOLD * 100:.0f} % ✗"
        )
        msg.exec()
