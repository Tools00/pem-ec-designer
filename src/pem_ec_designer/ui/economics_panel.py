"""EconomicsPanel — §4 of UX-VISION: LCOH live-readout with two sliders.

CapEx + Strompreis-Slider → recompute LCOH on every change. Receives the
current V_cell @ design_j from the MainWindow (`set_v_cell()`) so it can
update the LHV efficiency and re-evaluate.

ADR-005 §UI-Anbindung. Stays a pure widget: no physics imports beyond
the value-objects from `physics.lcoh` and `physics.efficiency`.
"""

# ruff: noqa: I001
from __future__ import annotations

from . import qt_env  # noqa: F401

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..physics.efficiency import lhv_efficiency
from ..physics.lcoh import LCOHInputs, levelised_cost_of_hydrogen


def _slider_row(
    minimum: int, maximum: int, default: int, suffix: str, step: int = 1
) -> tuple[QWidget, QSlider, QLabel]:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(minimum)
    slider.setMaximum(maximum)
    slider.setSingleStep(step)
    slider.setValue(default)
    label = QLabel(f"{default} {suffix}")
    label.setMinimumWidth(110)
    layout.addWidget(slider, stretch=1)
    layout.addWidget(label)
    return container, slider, label


class EconomicsPanel(QGroupBox):
    """LCOH live readout — CapEx slider + electricity slider + €/kg label.

    Defaults match `LCOHInputs()` (Schmidt-2017 anchor): CapEx 1100 €/kW,
    Strom 50 €/MWh. Slider ranges:

      - CapEx        : 400 – 3000 €/kW (step 50)
      - Strompreis   : 10 – 200 €/MWh  (step 5)

    The 5-fixed-economic-parameters (lifetime, discount, CF, OpEx-fraction,
    BoP-η) are kept at LCOHInputs defaults in v1.0 — exposed via API but
    not via UI yet.
    """

    # Emitted on slider change — useful for QSettings persistence later.
    parameters_changed = Signal(float, float)  # capex_eur_per_kw, electricity_eur_per_mwh

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Economics (LCOH)", parent)

        row_capex, self._slider_capex, self._label_capex = _slider_row(
            minimum=400, maximum=3000, default=1100, suffix="€/kW", step=50
        )
        self._slider_capex.valueChanged.connect(self._on_change)

        row_elec, self._slider_elec, self._label_elec = _slider_row(
            minimum=10, maximum=200, default=50, suffix="€/MWh", step=5
        )
        self._slider_elec.valueChanged.connect(self._on_change)

        self._lcoh_label = QLabel("LCOH —  (waiting for V_cell)")
        self._lcoh_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        self._breakdown_label = QLabel("")
        self._breakdown_label.setStyleSheet("color: #555;")

        form = QFormLayout()
        form.addRow("CapEx", row_capex)
        form.addRow("Strompreis", row_elec)

        outer = QVBoxLayout(self)
        outer.addLayout(form)
        outer.addWidget(self._lcoh_label)
        outer.addWidget(self._breakdown_label)

        self._v_cell_design: float | None = None

    # ── public API ─────────────────────────────────────────────────────

    def set_v_cell(self, v_cell: float) -> None:
        """Receive the current design-point cell voltage and recompute LCOH."""
        if v_cell <= 0:
            self._lcoh_label.setText("LCOH —  (invalid V_cell)")
            return
        self._v_cell_design = v_cell
        self._recompute()

    def current_inputs(self) -> LCOHInputs:
        return LCOHInputs(
            capex_eur_per_kw=float(self._slider_capex.value()),
            electricity_eur_per_mwh=float(self._slider_elec.value()),
        )

    def set_state(self, capex_eur_per_kw: float, electricity_eur_per_mwh: float) -> None:
        """Restore slider values without emitting signals."""
        # Clamp to slider ranges to avoid Qt silently rejecting out-of-range.
        capex = max(400, min(3000, int(round(capex_eur_per_kw))))
        elec = max(10, min(200, int(round(electricity_eur_per_mwh))))
        for sl in (self._slider_capex, self._slider_elec):
            sl.blockSignals(True)
        try:
            self._slider_capex.setValue(capex)
            self._slider_elec.setValue(elec)
        finally:
            for sl in (self._slider_capex, self._slider_elec):
                sl.blockSignals(False)
        self._label_capex.setText(f"{capex} €/kW")
        self._label_elec.setText(f"{elec} €/MWh")

    # ── internals ──────────────────────────────────────────────────────

    def _on_change(self) -> None:
        capex = self._slider_capex.value()
        elec = self._slider_elec.value()
        self._label_capex.setText(f"{capex} €/kW")
        self._label_elec.setText(f"{elec} €/MWh")
        self.parameters_changed.emit(float(capex), float(elec))
        if self._v_cell_design is not None:
            self._recompute()

    def _recompute(self) -> None:
        if self._v_cell_design is None:
            return
        eta = lhv_efficiency(self._v_cell_design)
        result = levelised_cost_of_hydrogen(eta, self.current_inputs())
        self._lcoh_label.setText(
            f"LCOH ≈ {result.lcoh_total:.2f} €/kg H₂"
            f"   (η_LHV = {eta:.2f}, V_cell = {self._v_cell_design:.2f} V)"
        )
        self._breakdown_label.setText(
            f"CapEx {result.capex_component:.2f}  ·  "
            f"OpEx {result.opex_component:.2f}  ·  "
            f"Strom {result.electricity_component:.2f}   "
            f"[€/kg]   |   SEC {result.sec_system_kwh_per_kg:.1f} kWh/kg"
        )
