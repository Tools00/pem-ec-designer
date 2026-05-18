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
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from ..assembly.source_collector import collect_source_keys
from ..assembly.stack import build_stack
from ..export.bibtex_export import write_bibtex_subset
from ..export.csv_export import CSVExportMetadata, write_polarisation_csv
from ..geometry import build_extruded
from ..materials import load_library
from ..physics.polarization import PolarisationCurve, polarisation_curve
from ..schema import Component
from .economics_panel import EconomicsPanel
from .onboarding_banner import OnboardingBanner
from .operating_panel import OperatingPanel
from .persistence import (
    default_settings,
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

        self._lib = load_library(library_dir)
        self._library_dir = Path(library_dir)
        self._last_curve: PolarisationCurve | None = None
        self._settings = default_settings()

        # Window size — restore (or default 1280×900).
        w, h = restore_window_size(self._settings)
        self.resize(w, h)

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
        self._viewer_group = _collapsible_group(
            "3D component preview (advanced)",
            components_viewer,
            default_open=False,
        )
        viewer_group = self._viewer_group

        section1_body = QWidget()
        s1_layout = QVBoxLayout(section1_body)
        s1_layout.setContentsMargins(0, 0, 0, 0)
        s1_layout.addWidget(self._composer)
        s1_layout.addWidget(viewer_group)

        # ── §2 Operating Point ─────────────────────────────────────────
        self._op_panel = OperatingPanel()
        self._op_panel.condition_changed.connect(self._on_condition_change)
        self._op_panel.design_j_changed.connect(self._on_design_j_change)

        # ── §3 Results ─────────────────────────────────────────────────
        self._plot_panel = PolarisationPanel()
        self._plot_panel.setMinimumHeight(360)
        self._plot_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # ── §4 Economics ───────────────────────────────────────────────
        self._econ_panel = EconomicsPanel()

        # ── §5 Export ──────────────────────────────────────────────────
        export_panel = QWidget()
        export_layout = QHBoxLayout(export_panel)
        export_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_csv = QPushButton("V–I CSV…")
        self._btn_csv.setToolTip("Polarisation sweep + loss breakdown + design-point<br>"
                                 "with self-documenting header (stack + sources cited).")
        self._btn_csv.clicked.connect(self._on_export_csv)
        self._btn_bib = QPushButton("Citations .bib…")
        self._btn_bib.setToolTip("Subset of library/sources.bib containing only<br>"
                                 "the BibTeX keys cited by the current stack.")
        self._btn_bib.clicked.connect(self._on_export_bibtex)
        export_layout.addWidget(self._btn_csv)
        export_layout.addWidget(self._btn_bib)
        export_layout.addStretch(1)
        export_layout.addWidget(QLabel(
            "<span style='color:#888'>STEP · STL · PDF → C+ Teil 2b</span>"
        ))

        # ── assemble single-page scroll area ───────────────────────────
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(8, 4, 8, 8)
        page_layout.setSpacing(8)
        page_layout.addWidget(_section("Stack Design", 1, section1_body))
        page_layout.addWidget(_section("Operating Point", 2, self._op_panel))
        page_layout.addWidget(_section("Results", 3, self._plot_panel))
        page_layout.addWidget(_section("Economics", 4, self._econ_panel))
        page_layout.addWidget(_section("Export", 5, export_panel))
        page_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)

        # ── Onboarding banner (UX-VISION §8) — shown unless flag set ─
        self._onboarding_banner = OnboardingBanner()
        self._onboarding_banner.dismissed.connect(self._on_onboarding_dismissed)

        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addWidget(header)
        outer_layout.addWidget(self._onboarding_banner)
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

        # Restore persisted state (silent fallback to defaults).
        self._restore_persisted_state()

        # Keyboard shortcuts per UX-VISION §11.
        self._wire_shortcuts()

        # Wire initial tooltips + run the first polarisation pass.
        self._refresh_composer_tooltips()
        self._recompute_polarisation()

    # ── shortcuts ─────────────────────────────────────────────────────

    def _wire_shortcuts(self) -> None:
        """Register UX-VISION §11 keyboard shortcuts (v1.0 subset).

        Cmd+E   → Export V–I CSV
        Cmd+D   → Toggle 3D component preview
        Cmd+R   → Reset stack + operating point + LCOH to defaults
        ?       → Help dialog with shortcut list
        Cmd+Q   → Quit (Qt default)
        """
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self._on_export_csv)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self._toggle_3d_preview)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self._reset_to_defaults)
        QShortcut(QKeySequence("?"), self, activated=self._show_help)
        QShortcut(QKeySequence("Shift+?"), self, activated=self._show_help)

    def _toggle_3d_preview(self) -> None:
        self._viewer_group.setChecked(not self._viewer_group.isChecked())

    def _reset_to_defaults(self) -> None:
        if QMessageBox.question(
            self, "Reset",
            "Reset stack, operating point and LCOH parameters to defaults?\n"
            "(Window size and onboarding flag are kept.)",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._settings.remove("stack")
        self._settings.remove("op")
        self._settings.remove("lcoh")
        self._settings.sync()
        # Re-apply defaults by reading from the (now empty) settings.
        self._composer.set_state(restore_stack(self._settings))
        T_C, ph2, po2, j = restore_operating_point(self._settings)
        self._op_panel.set_state(T_C, ph2, po2, j)
        capex, elec = restore_lcoh(self._settings)
        self._econ_panel.set_state(capex, elec)
        self._refresh_composer_tooltips()
        self._recompute_polarisation()
        self.statusBar().showMessage("Reset to defaults.")

    def _show_help(self) -> None:
        QMessageBox.information(
            self, "Keyboard shortcuts",
            "<b>Cmd+E</b>  Export V–I CSV<br>"
            "<b>Cmd+D</b>  Toggle 3D component preview<br>"
            "<b>Cmd+R</b>  Reset to defaults<br>"
            "<b>Cmd+Q</b>  Quit<br>"
            "<b>?</b>      This help<br><br>"
            "All sliders and dropdowns recompute the polarisation curve live.<br>"
            "Hover any value for its BibTeX source."
        )

    # ── onboarding ────────────────────────────────────────────────────

    def _on_onboarding_dismissed(self) -> None:
        show3d, _ = restore_ui_flags(self._settings)
        save_ui_flags(self._settings, show3d=show3d, onboarding_seen=True)

    # ── persistence ───────────────────────────────────────────────────

    def _restore_persisted_state(self) -> None:
        """Restore stack / operating / lcoh values from QSettings.

        Each block validates inputs (composer rejects unknown IDs, sliders
        clamp out-of-range values) — corrupt or stale settings degrade
        gracefully to defaults.
        """
        stack_ids = restore_stack(self._settings)
        if any(stack_ids.values()):
            self._composer.set_state(stack_ids)
        T_C, p_h2_bar, p_o2_bar, j_design = restore_operating_point(self._settings)
        self._op_panel.set_state(T_C, p_h2_bar, p_o2_bar, j_design)
        capex, electricity = restore_lcoh(self._settings)
        self._econ_panel.set_state(capex, electricity)

        # Onboarding-banner visibility per UX-VISION §8.
        _, onboarding_seen = restore_ui_flags(self._settings)
        self._onboarding_banner.setVisible(not onboarding_seen)

        # Wire the persistence-save side after restore so we don't
        # immediately re-write defaults on top of the restored values.
        self._econ_panel.parameters_changed.connect(self._persist_lcoh)

    def _persist_stack(self) -> None:
        save_stack(self._settings, self._composer.current_selection())

    def _persist_operating(self) -> None:
        T_K, p_h2, p_o2 = self._op_panel.current_values()
        save_operating_point(
            self._settings,
            T_C=T_K - 273.15,
            p_h2_bar=p_h2 / 1e5,
            p_o2_bar=p_o2 / 1e5,
            j_design_A_per_cm2=self._op_panel.current_design_j() / 1e4,
        )

    def _persist_lcoh(self, capex: float, electricity: float) -> None:
        save_lcoh(self._settings, capex, electricity)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_settings"):
            save_window_size(self._settings, self.width(), self.height())

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
        self._last_curve = curve
        title = f"PEM-EC cell @ {T_K - 273.15:.0f} °C · p_H2={p_h2/1e5:.0f} bar · p_O2={p_o2/1e5:.0f} bar"

        design_j_A_per_m2 = self._op_panel.current_design_j()
        design_j_cm2 = design_j_A_per_m2 / 1e4
        self._plot_panel.set_curve(curve, title=title, design_j_A_per_cm2=design_j_cm2)

        design_point = min(curve.points, key=lambda p: abs(p.j - design_j_A_per_m2))
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
        self._persist_operating()
        self._onboarding_banner.dismiss()

    def _on_composer_change(self) -> None:
        self._refresh_composer_tooltips()
        self._recompute_polarisation()
        self._persist_stack()
        self._onboarding_banner.dismiss()

    def _on_design_j_change(self, design_j_A_per_m2: float) -> None:
        """Design-j slider moved — repick design point on the cached curve.

        Does NOT rebuild the stack or recompute V(j) — only the marker /
        LCOH / Validation-Badge read-outs change. UX-VISION §6.2.
        """
        self._persist_operating()
        if self._last_curve is None or not self._last_curve.points:
            return
        design_j_cm2 = design_j_A_per_m2 / 1e4
        # Re-draw with new marker (title preserved by reconstructing from current sliders).
        T_K, p_h2, p_o2 = self._op_panel.current_values()
        title = f"PEM-EC cell @ {T_K - 273.15:.0f} °C · p_H2={p_h2/1e5:.0f} bar · p_O2={p_o2/1e5:.0f} bar"
        self._plot_panel.set_curve(self._last_curve, title=title, design_j_A_per_cm2=design_j_cm2)
        design_point = min(self._last_curve.points, key=lambda p: abs(p.j - design_j_A_per_m2))
        self._econ_panel.set_v_cell(design_point.v_cell)
        self._validation_badge.set_voltage(design_point.v_cell)

    # ── §5 Export handlers ────────────────────────────────────────────

    def _build_csv_metadata(self) -> CSVExportMetadata:
        sel = self._composer.current_selection()
        T_K, p_h2, p_o2 = self._op_panel.current_values()
        components = [
            self._lib.components.get(cid) for cid in (
                sel.membrane_id, sel.anode_cl_id, sel.cathode_cl_id,
                sel.anode_gdl_id, sel.cathode_gdl_id,
                sel.anode_bpp_id, sel.cathode_bpp_id,
            ) if cid
        ]
        materials = [
            self._lib.materials.get(mid) for mid in (
                sel.membrane_material_id,
                sel.anode_catalyst_material_id,
                sel.cathode_catalyst_material_id,
            ) if mid
        ]
        sources = collect_source_keys(components, materials)
        return CSVExportMetadata(
            T_celsius=T_K - 273.15,
            p_h2_bar=p_h2 / 1e5,
            p_o2_bar=p_o2 / 1e5,
            stack_components={
                "membrane": sel.membrane_id,
                "anode_cl": sel.anode_cl_id,
                "cathode_cl": sel.cathode_cl_id,
                "anode_gdl": sel.anode_gdl_id,
                "cathode_gdl": sel.cathode_gdl_id,
                "anode_bpp": sel.anode_bpp_id,
                "cathode_bpp": sel.cathode_bpp_id,
            },
            stack_materials={
                "membrane": sel.membrane_material_id,
                "anode_catalyst": sel.anode_catalyst_material_id,
                "cathode_catalyst": sel.cathode_catalyst_material_id,
            },
            sources_cited=sources,
            design_j_A_per_cm2=self._op_panel.current_design_j() / 1e4,
        )

    def _on_export_csv(self) -> None:
        if self._last_curve is None or not self._last_curve.points:
            QMessageBox.information(self, "Export", "No polarisation curve to export yet.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export V–I CSV", "polarisation.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            write_polarisation_csv(self._last_curve, self._build_csv_metadata(), Path(path))
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        self.statusBar().showMessage(f"CSV exported → {path}")

    def _on_export_bibtex(self) -> None:
        sel = self._composer.current_selection()
        components = [self._lib.components.get(cid) for cid in (
            sel.membrane_id, sel.anode_cl_id, sel.cathode_cl_id,
            sel.anode_gdl_id, sel.cathode_gdl_id,
            sel.anode_bpp_id, sel.cathode_bpp_id,
        ) if cid]
        materials = [self._lib.materials.get(mid) for mid in (
            sel.membrane_material_id,
            sel.anode_catalyst_material_id,
            sel.cathode_catalyst_material_id,
        ) if mid]
        keys = collect_source_keys(components, materials)
        if not keys:
            QMessageBox.information(self, "Export", "No BibTeX keys cited by current stack.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export cited sources (.bib)", "cited_sources.bib", "BibTeX (*.bib)"
        )
        if not path:
            return
        try:
            found = write_bibtex_subset(
                self._library_dir / "sources.bib", keys, Path(path)
            )
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return
        missing = keys - found
        msg = f"BibTeX exported → {path} ({len(found)} entries)"
        if missing:
            msg += f"  ·  {len(missing)} requested key(s) not in sources.bib: {', '.join(sorted(missing))}"
        self.statusBar().showMessage(msg)
