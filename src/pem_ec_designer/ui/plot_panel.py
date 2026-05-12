"""PolarisationPanel — Matplotlib FigureCanvas embedded in a QWidget.

ADR-001 layer rule: this file imports PySide6 + matplotlib but NEVER
the physics modules' state. Pure plot widget — caller hands it a
`PolarisationCurve`, it draws.
"""

# ruff: noqa: I001  -- qt_env MUST precede PySide6 imports (UI-LAUNCH-NOTES §1)
from __future__ import annotations

from . import qt_env  # noqa: F401

import numpy as np
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..physics.polarization import PolarisationCurve


class PolarisationPanel(QWidget):
    """V–I curve + stacked loss decomposition. Re-plot via `set_curve()`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._fig = Figure(figsize=(8, 4), tight_layout=True)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

        self._ax_vi = self._fig.add_subplot(1, 2, 1)
        self._ax_decomp = self._fig.add_subplot(1, 2, 2)
        self._draw_empty()

    def _draw_empty(self) -> None:
        for ax in (self._ax_vi, self._ax_decomp):
            ax.clear()
            ax.text(
                0.5, 0.5, "no curve loaded", ha="center", va="center",
                transform=ax.transAxes, color="grey", fontsize=11,
            )
            ax.set_xticks([])
            ax.set_yticks([])
        self._canvas.draw_idle()

    def set_curve(self, curve: PolarisationCurve, title: str = "") -> None:
        """Render V(j) + waterfall decomposition for the given curve."""
        if not curve.points:
            self._draw_empty()
            return

        j_cm2 = np.array([p.j for p in curve.points]) / 1e4   # A/m² → A/cm²
        v = np.array([p.v_cell for p in curve.points])
        e_rev = np.array([p.e_rev for p in curve.points])
        eta_oer = np.array([p.eta_oer for p in curve.points])
        eta_her = np.array([p.eta_her for p in curve.points])
        eta_ohm = np.array([p.eta_ohm for p in curve.points])

        # Left: V–I curve
        ax = self._ax_vi
        ax.clear()
        ax.plot(j_cm2, v, "k-", lw=2.5, label="V_cell")
        ax.axhline(1.229, color="grey", ls="--", lw=0.8, label="E_rev,STP")
        ax.set_xlabel("current density  j  (A/cm²)")
        ax.set_ylabel("cell voltage  V  (V)")
        ax.set_title(title or "Polarisation curve")
        ax.legend(loc="lower right", fontsize=9)
        ax.grid(True, alpha=0.3)

        # Mark V(1) and V(2) if in range
        for j_target in (1.0, 2.0):
            if j_cm2.min() <= j_target <= j_cm2.max():
                idx = int(np.argmin(np.abs(j_cm2 - j_target)))
                ax.plot([j_target], [v[idx]], "ro", ms=5)
                ax.annotate(
                    f"{v[idx]:.3f} V @ {j_target:.0f} A/cm²",
                    xy=(j_target, v[idx]),
                    xytext=(8, -12),
                    textcoords="offset points",
                    fontsize=8,
                    color="red",
                )

        # Right: stacked loss decomposition
        ax = self._ax_decomp
        ax.clear()
        ax.fill_between(j_cm2, 0, e_rev, label=f"E_rev ({e_rev[0]:.3f} V)",
                        color="#4F81BD", alpha=0.75)
        ax.fill_between(j_cm2, e_rev, e_rev + eta_oer, label="η_OER",
                        color="#C0504D", alpha=0.8)
        ax.fill_between(j_cm2, e_rev + eta_oer, e_rev + eta_oer + eta_her, label="η_HER",
                        color="#9BBB59", alpha=0.8)
        ax.fill_between(j_cm2, e_rev + eta_oer + eta_her, v, label="η_ohmic",
                        color="#F79646", alpha=0.8)
        ax.plot(j_cm2, v, "k-", lw=1.5)
        ax.set_xlabel("current density  j  (A/cm²)")
        ax.set_ylabel("V  (V)")
        ax.set_title("Loss decomposition")
        ax.legend(loc="lower right", fontsize=8)
        ax.grid(True, alpha=0.3)

        self._canvas.draw_idle()
