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
    """Three sliders: cell T (°C), p_H2 (bar), p_O2 (bar)."""

    condition_changed = Signal(float, float, float)  # T_K, p_h2_Pa, p_o2_Pa

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

        form = QFormLayout()
        form.addRow("Temperature", row_t)
        form.addRow("p (H2, cathode)", row_ph2)
        form.addRow("p (O2, anode)", row_po2)

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

    def current_values(self) -> tuple[float, float, float]:
        """(T_K, p_h2_Pa, p_o2_Pa) — for initial render before any slider move."""
        return (
            float(self._slider_t.value()) + 273.15,
            float(self._slider_ph2.value()) * 1e5,
            float(self._slider_po2.value()) * 1e5,
        )
