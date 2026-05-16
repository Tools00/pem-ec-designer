"""MainWindow — single-page notebook layout per UX-VISION §4.

Top header with title + Validation-Badge (right-aligned). Below that,
a vertical scroll area with five sections (P1 „Lesereihenfolge = Pipeline"):

    §1 Stack Design     — StackComposer + collapsible 3D component viewer
    §2 Operating Point  — T/p sliders
    §3 Results          — V–I curve + loss waterfall
    §4 Economics        — LCOH live read-out
    §5 Export           — placeholder for v0.1 (STEP / CSV / BibTeX buttons land here)

Tabs were the v0 abbreviation; UX-VISION §5 P1 demands top-to-bottom
cause-and-effect, not tab-hopping.
"""

# ruff: noqa: I001  -- qt_env MUST precede PySide6 imports (see UI-LAUNCH-NOTES §1)
from __future__ import annotations

from pathlib import Path

from . import qt_env  # noqa: F401

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from ..assembly.stack import build_stack
from ..geometry import build_extruded
from ..materials import load_library
from ..physics.polarization import polarisation_curve
from ..schema import Component
from .economics_panel import EconomicsPanel
from .operating_panel import OperatingPanel
from .plot_panel import PolarisationPanel
from .source_tooltip import format_thickness_tooltip
from .stack_composer import StackComposer, StackSelection
from .validation_badge import ValidationBadge
from .viewer import part_to_mesh

# Design current density for LCOH + validation read-out (1 A/cm² = 1e4 A/m²).
_DESIGN_J_A_PER_M2: float = 1.0e4


def _section(title: str, number: int, body: QWidget) -> QGroupBox:
    """Wrap a section widget in a labelled GroupBox (§N · Title)."""
    box = QGroupBox(f"§{number}  ·  {title}")
    box.setStyleSheet("QGroupBox { font-weight: bold; }")
    layout = QVBoxLayout(box)
    layout.setContentsMargins(8, 14, 8, 8)
    layout.addWidget(body)
    return box


def _collapsible_group(title: str, body: QWidget, default_open: bool = False) -> QGroupBox:
    """A checkable QGroupBox that hides its body when unchecked.

    Used for the 3D component preview in §1 — present but not eating
    vertical real-estate by default (UX-VISION §4 Window-Constraints).
    """
    box = QGroupBox(title)
    box.setCheckable(True)
    box.setChecked(default_open)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(8, 14, 8, 8)
    layout.addWidget(body)
    body.setVisible(default_open)
    box.toggled.connect(body.setVisible)
    return box


class MainWindow(QMainWindow):
    def __init__(self, library_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("pem-ec-designer v0")
        self.resize(1280, 900)

        self._lib = load_library(library_dir)

        # ── Header (title left, validation badge right) ────────────────
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 6, 10, 6)
        title_label = QLabel("PEM-EC Designer")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self._validation_badge = ValidationBadge()
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self._validation_badge)

        # ── §1 Stack Design: composer + collapsible 3D viewer ──────────
        self._composer = StackComposer(self._lib)
        self._composer.selection_changed.connect(self._on_composer_change)

        # 3D component viewer (the old "Components" tab content) is now
        # the §1 collapsible detail — default closed.
        components_viewer = self._build_components_viewer()
        viewer_group = _collapsible_group(
            "3D component preview (advanced)",
            components_viewer,
            default_open=False,
        )

        section1_body = QWidget()
        s1_layout = QVBoxLayout(section1_body)
        s1_layout.setContentsMargins(0, 0, 0, 0)
        s1_layout.addWidget(self._composer)
        s1_layout.addWidget(viewer_group)

        # ── §2 Operating Point ─────────────────────────────────────────
        self._op_panel = OperatingPanel()
        self._op_panel.condition_changed.connect(self._on_condition_change)

        # ── §3 Results ─────────────────────────────────────────────────
        self._plot_panel = PolarisationPanel()
        self._plot_panel.setMinimumHeight(360)
        self._plot_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # ── §4 Economics ───────────────────────────────────────────────
        self._econ_panel = EconomicsPanel()

        # ── §5 Export (placeholder) ────────────────────────────────────
        export_placeholder = QLabel(
            "Export (STEP · STL · V–I CSV · Citations .bib · PDF) — Pfad C+ Teil 2"
        )
        export_placeholder.setStyleSheet("color: #888; padding: 8px;")

        # ── assemble single-page scroll area ───────────────────────────
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 4, 8, 8)
        page_layout.setSpacing(8)
        page_layout.addWidget(_section("Stack Design", 1, section1_body))
        page_layout.addWidget(_section("Operating Point", 2, self._op_panel))
        page_layout.addWidget(_section("Results", 3, self._plot_panel))
        page_layout.addWidget(_section("Economics", 4, self._econ_panel))
        page_layout.addWidget(_section("Export", 5, export_placeholder))
        page_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(header)
        outer_layout.addWidget(scroll, stretch=1)
        self.setCentralWidget(outer)

        self.statusBar().showMessage(
            f"Library loaded: {len(self._lib.components)} components, "
            f"{len(self._lib.materials)} materials."
        )

        # Auto-select first item in the 3D viewer list so it isn't empty
        # if the user opens the collapsible.
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

        # Wire initial tooltips + run the first polarisation pass.
        self._refresh_composer_tooltips()
        self._recompute_polarisation()

    # ── §1 Stack-Composer tooltips ────────────────────────────────────

    def _refresh_composer_tooltips(self) -> None:
        """Push source tooltips onto the StackComposer ComboBoxes after a change."""
        sel = self._composer.current_selection()
        L = self._lib
        # Component dropdowns: cite thickness source.
        for cb, cid in [
            (self._composer._cb_membrane, sel.membrane_id),
            (self._composer._cb_anode_cl, sel.anode_cl_id),
            (self._composer._cb_cathode_cl, sel.cathode_cl_id),
            (self._composer._cb_anode_gdl, sel.anode_gdl_id),
            (self._composer._cb_cathode_gdl, sel.cathode_gdl_id),
            (self._composer._cb_anode_bpp, sel.anode_bpp_id),
            (self._composer._cb_cathode_bpp, sel.cathode_bpp_id),
        ]:
            if cid and cid in L.components:
                cb.setToolTip(format_thickness_tooltip(L.components[cid]))
            else:
                cb.setToolTip("")

    # ── 3D component viewer (formerly the Components tab) ─────────────

    def _build_components_viewer(self) -> QWidget:
        self._list = QListWidget()
        sorted_ids = sorted(
            self._lib.components,
            key=lambda c: self._lib.components[c].thickness.value.value_si,
        )
        for cid in sorted_ids:
            comp = self._lib.components[cid]
            t_um = comp.thickness.value.value_si * 1e6
            label = f"{cid}    {t_um:>6.1f} um"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, cid)
            item.setToolTip(format_thickness_tooltip(comp))
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_selection)

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
        splitter.setMinimumHeight(380)
        return splitter

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
        item = self._list.currentItem()
        if item is not None:
            self._on_selection(item, None)

    # ── §2/§3/§4 simulation pipeline ──────────────────────────────────

    def _build_stack_from_composer(self, T_K: float, p_h2_Pa: float, p_o2_Pa: float):
        sel: StackSelection = self._composer.current_selection()
        L = self._lib
        return build_stack(
            membrane=L.components[sel.membrane_id],
            membrane_material=L.materials[sel.membrane_material_id],
            anode_catalyst_material=L.materials[sel.anode_catalyst_material_id],
            cathode_catalyst_material=L.materials[sel.cathode_catalyst_material_id],
            anode_cl=L.components.get(sel.anode_cl_id) if sel.anode_cl_id else None,
            cathode_cl=L.components.get(sel.cathode_cl_id) if sel.cathode_cl_id else None,
            anode_gdl=L.components.get(sel.anode_gdl_id) if sel.anode_gdl_id else None,
            cathode_gdl=L.components.get(sel.cathode_gdl_id) if sel.cathode_gdl_id else None,
            anode_bpp=L.components.get(sel.anode_bpp_id) if sel.anode_bpp_id else None,
            cathode_bpp=L.components.get(sel.cathode_bpp_id) if sel.cathode_bpp_id else None,
            T=T_K, p_h2=p_h2_Pa, p_o2=p_o2_Pa,
        )

    def _recompute_polarisation(self) -> None:
        T_K, p_h2, p_o2 = self._op_panel.current_values()
        try:
            build = self._build_stack_from_composer(T_K, p_h2, p_o2)
        except (KeyError, ValueError) as exc:
            self.statusBar().showMessage(f"Simulation setup failed: {exc}")
            return

        j_values = np.linspace(1.0, 6e4, 200).tolist()
        curve = polarisation_curve(
            j_values=j_values,
            kinetics=build.kinetics,
            op=build.operating_point,
            ohmic=build.ohmic,
        )
        title = f"PEM-EC cell @ {T_K - 273.15:.0f} °C · p_H2={p_h2/1e5:.0f} bar · p_O2={p_o2/1e5:.0f} bar"
        self._plot_panel.set_curve(curve, title=title)

        design_point = min(curve.points, key=lambda p: abs(p.j - _DESIGN_J_A_PER_M2))
        self._econ_panel.set_v_cell(design_point.v_cell)
        self._validation_badge.set_voltage(design_point.v_cell)

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

    def _on_composer_change(self) -> None:
        self._refresh_composer_tooltips()
        self._recompute_polarisation()
