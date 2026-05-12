"""MainWindow v0 — sidebar with library components, embedded VTK viewer.

Scope (deliberately small):
- Left: list of all component IDs from the library.
- Right: pyvistaqt QtInteractor renders the selected component.
- Status bar: shows component name + spec source.
- File > Quit.

Anything else (multi-select, transformations, stack assembly, save) is
out of scope for v0.
"""

# ruff: noqa: I001  -- qt_env MUST precede PySide6 imports (see UI-LAUNCH-NOTES §1)
from __future__ import annotations

from pathlib import Path

from . import qt_env  # noqa: F401

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from ..assembly.stack import build_stack
from ..geometry import build_extruded
from ..materials import load_library
from ..physics.polarization import polarisation_curve
from ..schema import Component
from .operating_panel import OperatingPanel
from .plot_panel import PolarisationPanel
from .viewer import part_to_mesh


class MainWindow(QMainWindow):
    def __init__(self, library_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("pem-ec-designer v0")
        self.resize(1100, 700)

        self._lib = load_library(library_dir)

        # Sort by thickness so the list order mirrors what the viewer
        # shows — user can verify visual scaling against the numbers.
        self._list = QListWidget()
        sorted_ids = sorted(
            self._lib.components,
            key=lambda c: self._lib.components[c].thickness.value.value_si,
        )
        for cid in sorted_ids:
            comp = self._lib.components[cid]
            t_um = comp.thickness.value.value_si * 1e6  # m -> um
            label = f"{cid}    {t_um:>6.1f} um"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cid)
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_selection)

        # Aspect ratio of real PEM components is brutal (membrane: 50 mm
        # diameter * 0.025 mm thick = 2000:1). Z-exaggeration toggle is
        # the standard fix in geo / wafer viewers — purely visual, the
        # underlying geometry stays untouched.
        self._z_exag = QCheckBox("Exaggerate Z x 100 (visual only)")
        self._z_exag.setChecked(True)
        self._z_exag.toggled.connect(self._rerender_current)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(self._z_exag)
        sidebar_layout.addWidget(self._list, stretch=1)

        self._plotter = QtInteractor(self)
        self._plotter.set_background("white")
        self._plotter.add_axes()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self._plotter.interactor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 840])

        # ─── Simulation tab ──────────────────────────────────────────
        # Builds a default stack from the Library and runs ADR-004
        # physics on the user-selected operating conditions.
        self._op_panel = OperatingPanel()
        self._op_panel.condition_changed.connect(self._on_condition_change)

        self._plot_panel = PolarisationPanel()

        sim_widget = QWidget()
        sim_layout = QVBoxLayout(sim_widget)
        sim_layout.setContentsMargins(6, 6, 6, 6)
        sim_layout.addWidget(self._op_panel)
        sim_layout.addWidget(self._plot_panel, stretch=1)

        tabs = QTabWidget()
        tabs.addTab(splitter, "Components")
        tabs.addTab(sim_widget, "Simulation")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage(
            f"Library loaded: {len(self._lib.components)} components, "
            f"{len(self._lib.materials)} materials."
        )

        # Auto-select first item so the viewer is never empty on launch.
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

        # Initial polarisation plot.
        self._recompute_polarisation()

    def _on_selection(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        cid = current.data(Qt.ItemDataRole.UserRole)
        component: Component = self._lib.components[cid]

        try:
            part = build_extruded(component)
        except (ValueError, NotImplementedError) as exc:
            self.statusBar().showMessage(f"{cid}: cannot render — {exc}")
            self._plotter.clear()
            return

        mesh = part_to_mesh(part)
        if self._z_exag.isChecked():
            mesh = mesh.scale([1.0, 1.0, 100.0], inplace=False)
        self._plotter.clear()
        self._plotter.add_axes()
        self._plotter.add_mesh(mesh, color="cornflowerblue", show_edges=True)
        self._plotter.reset_camera()
        self._plotter.view_isometric()
        self._plotter.render()

        thickness_mm = component.thickness.value.value_si * 1000.0
        z_note = "  |  Zx100" if self._z_exag.isChecked() else ""
        self.statusBar().showMessage(
            f"{cid}  ·  {component.name}  ·  thickness {thickness_mm:.3f} mm  "
            f"·  source {component.thickness.source}{z_note}"
        )

    def _rerender_current(self) -> None:
        """Re-render the currently selected item, e.g. after a Z-toggle."""
        item = self._list.currentItem()
        if item is not None:
            self._on_selection(item, None)

    # ── Simulation tab ──────────────────────────────────────────────

    def _build_default_stack(self, T_K: float, p_h2_Pa: float, p_o2_Pa: float):
        """Hardcoded reference stack for v0 (no Stack-Composer yet).

        Components and materials are picked from the Library by ID;
        if anything is missing the user sees the error in the status bar.
        """
        L = self._lib
        return build_stack(
            membrane=L.components["membrane.nafion.212"],
            membrane_material=L.materials["nafion-1100"],
            anode_catalyst_material=L.materials["iro2-tio2-catalyst"],
            cathode_catalyst_material=L.materials["pt-c-catalyst"],
            anode_gdl=L.components.get("gdl.sgl.39bb"),
            cathode_gdl=L.components.get("gdl.sgl.39bb"),
            anode_bpp=L.components.get("bpp.poco.axf5q_5mm"),
            cathode_bpp=L.components.get("bpp.poco.axf5q_5mm"),
            T=T_K, p_h2=p_h2_Pa, p_o2=p_o2_Pa,
        )

    def _recompute_polarisation(self) -> None:
        """Pull current operating conditions, rebuild stack, re-plot V(j)."""
        T_K, p_h2, p_o2 = self._op_panel.current_values()
        try:
            build = self._build_default_stack(T_K, p_h2, p_o2)
        except (KeyError, ValueError) as exc:
            self.statusBar().showMessage(f"Simulation setup failed: {exc}")
            return

        j_values = np.linspace(1.0, 6e4, 200).tolist()  # 1 A/m² → 6 A/cm²
        curve = polarisation_curve(
            j_values=j_values,
            kinetics=build.kinetics,
            op=build.operating_point,
            ohmic=build.ohmic,
        )
        title = f"PEM-EC cell @ {T_K - 273.15:.0f} °C · p_H2={p_h2/1e5:.0f} bar · p_O2={p_o2/1e5:.0f} bar"
        self._plot_panel.set_curve(curve, title=title)

        # Status: ASR breakdown + skipped layers (transparency).
        asr_total_ohm_cm2 = sum(c.asr for c in build.ohmic) / 1e-4
        msg = (
            f"Stack: {len(build.ohmic)} ohmic layers, total ASR ≈ "
            f"{asr_total_ohm_cm2:.3f} Ω·cm². "
        )
        if build.skipped_layers:
            msg += f"Skipped: {len(build.skipped_layers)} (no ASR cited)."
        self.statusBar().showMessage(msg)

    def _on_condition_change(self, T_K: float, p_h2_Pa: float, p_o2_Pa: float) -> None:
        self._recompute_polarisation()
