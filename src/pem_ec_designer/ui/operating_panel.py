"""OperatingPanel — T/p sliders for live simulation replot.

Emits `condition_changed` whenever any slider moves. The caller wires
that signal into the recompute pipeline.
"""

# ruff: noqa: I001
from __future__ import annotations

from . import qt_env  # noqa: F401

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt


def _slider_row(
    minimum: int, maximum: int, default: int, fmt: str, suffix: str
) -> tuple[QWidget, QSlider, QLabel]:
    """A horizontal (slider + value-label) row.

    Sliders are integer-only; the caller converts to float at the boundary.
    """
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(minimum)
    slider.setMaximum(maximum)
    slider.setValue(default)
    label = QLabel(fmt.format(default) + f" {suffix}")
    label.setMinimumWidth(80)
    layout.addWidget(slider, stretch=1)
    layout.addWidget(label)
    return container, slider, label


class OperatingPanel(QGroupBox):
    """Four sliders: cell T (°C), p_H2 (bar), p_O2 (bar), design_j (A/cm²)."""

    # T_K, p_h2_Pa, p_o2_Pa — fires when *physical* conditions change.
    # Design-j is on a separate signal because it doesn't rebuild the
    # stack, only repositions the marker / LCOH / validation read-out.
    condition_changed = Signal(float, float, float)
    design_j_changed = Signal(float)  # A/m² (SI for consistency with physics layer)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Operating conditions", parent)

        # T: 50–95 °C
        row_t, self._slider_t, self._label_t = _slider_row(50, 95, 80, "{:>3d}", "°C")
        self._slider_t.valueChanged.connect(self._on_change)

        # p_H2: 1–30 bar
        row_ph2, self._slider_ph2, self._label_ph2 = _slider_row(1, 30, 1, "{:>3d}", "bar")
        self._slider_ph2.valueChanged.connect(self._on_change)

        # p_O2: 1–30 bar
        row_po2, self._slider_po2, self._label_po2 = _slider_row(1, 30, 1, "{:>3d}", "bar")
        self._slider_po2.valueChanged.connect(self._on_change)

        # design_j: 0.1–4.0 A/cm² in 0.1 steps (integer slider 1–40, /10).
        # 1.0 A/cm² is the default because that is the Bernt-2016 anchor
        # for the Validation-Badge.
        row_j, self._slider_j, self._label_j = _slider_row(1, 40, 10, "{:>4.1f}", "A/cm²")
        # Override the formatter — we divide by 10 to get fractional A/cm².
        self._label_j.setText("1.0 A/cm²")
        self._slider_j.valueChanged.connect(self._on_design_j_change)

        form = QFormLayout()
        form.addRow("Temperature", row_t)
        form.addRow("p (H2, cathode)", row_ph2)
        form.addRow("p (O2, anode)", row_po2)
        form.addRow("Design  j", row_j)

        outer = QVBoxLayout(self)
        outer.addLayout(form)

    def _on_change(self) -> None:
        T_C = self._slider_t.value()
        p_h2_bar = self._slider_ph2.value()
        p_o2_bar = self._slider_po2.value()
        self._label_t.setText(f"{T_C:>3d} °C")
        self._label_ph2.setText(f"{p_h2_bar:>3d} bar")
        self._label_po2.setText(f"{p_o2_bar:>3d} bar")
        self.condition_changed.emit(
            float(T_C) + 273.15,    # K
            float(p_h2_bar) * 1e5,  # Pa
            float(p_o2_bar) * 1e5,  # Pa
        )

    def _on_design_j_change(self) -> None:
        j_A_per_cm2 = self._slider_j.value() / 10.0
        self._label_j.setText(f"{j_A_per_cm2:>4.1f} A/cm²")
        self.design_j_changed.emit(j_A_per_cm2 * 1e4)  # A/m²

    def current_values(self) -> tuple[float, float, float]:
        """(T_K, p_h2_Pa, p_o2_Pa) — for initial render before any slider move."""
        return (
            float(self._slider_t.value()) + 273.15,
            float(self._slider_ph2.value()) * 1e5,
            float(self._slider_po2.value()) * 1e5,
        )

    def current_design_j(self) -> float:
        """Current design-current-density in A/m² (SI)."""
        return self._slider_j.value() / 10.0 * 1e4

    def set_state(
        self,
        T_C: float,
        p_h2_bar: float,
        p_o2_bar: float,
        j_design_A_per_cm2: float,
    ) -> None:
        """Restore slider values without emitting signals (avoids cascade)."""
        for sl in (self._slider_t, self._slider_ph2, self._slider_po2, self._slider_j):
            sl.blockSignals(True)
        try:
            self._slider_t.setValue(int(round(T_C)))
            self._slider_ph2.setValue(int(round(p_h2_bar)))
            self._slider_po2.setValue(int(round(p_o2_bar)))
            self._slider_j.setValue(max(1, min(40, int(round(j_design_A_per_cm2 * 10)))))
        finally:
            for sl in (self._slider_t, self._slider_ph2, self._slider_po2, self._slider_j):
                sl.blockSignals(False)
        # Refresh labels manually.
        self._label_t.setText(f"{self._slider_t.value():>3d} °C")
        self._label_ph2.setText(f"{self._slider_ph2.value():>3d} bar")
        self._label_po2.setText(f"{self._slider_po2.value():>3d} bar")
        self._label_j.setText(f"{self._slider_j.value() / 10.0:>4.1f} A/cm²")
