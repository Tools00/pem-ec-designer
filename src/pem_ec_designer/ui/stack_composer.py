"""StackComposer — §1 of UX-VISION: 9 Library-Filter-Dropdowns.

7 component slots + 2 catalyst-material slots. Each ComboBox is filled
from `assembly.library_filter`. Any selection change emits a single
`selection_changed` signal — MainWindow re-runs polarisation + LCOH.

ADR-006 §UI-Anbindung. Polish (skipped-layer-badge, ASR-summary) is
Pfad C+ and stays out of this widget for now.
"""

# ruff: noqa: I001
from __future__ import annotations

from dataclasses import dataclass

from . import qt_env  # noqa: F401

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QWidget,
)

from ..assembly import library_filter as lf
from ..materials.loader import Library


@dataclass(frozen=True)
class StackSelection:
    """Plain-data snapshot of one composer state — what MainWindow consumes."""

    membrane_id: str
    membrane_material_id: str
    anode_catalyst_material_id: str
    cathode_catalyst_material_id: str
    anode_cl_id: str | None
    cathode_cl_id: str | None
    anode_gdl_id: str | None
    cathode_gdl_id: str | None
    anode_bpp_id: str | None
    cathode_bpp_id: str | None


# Default selection — reproduces the v0 hardcoded reference stack so
# users see the same V–I curve on first open (P7 in UX-VISION).
_DEFAULT_SELECTION_HINTS: dict[str, str] = {
    "membrane": "membrane.nafion.212",
    "membrane_material": "nafion-1100",
    "anode_catalyst_material": "iro2-tio2-catalyst",
    "cathode_catalyst_material": "pt-c-catalyst",
    "anode_cl": "anode_cl.bernt2016.optimal",
    "cathode_cl": "cathode_cl.zhang2024.baseline",
    "anode_gdl": "gdl.sgl.39bb",
    "cathode_gdl": "gdl.sgl.39bb",
    "anode_bpp": "bpp.poco.axf5q_5mm",
    "cathode_bpp": "bpp.poco.axf5q_5mm",
}


def _populate(combo: QComboBox, ids: list[str], default_id: str | None) -> None:
    """Fill a ComboBox; preselect default if present."""
    combo.clear()
    for i in ids:
        combo.addItem(i, userData=i)
    if default_id and default_id in ids:
        combo.setCurrentIndex(ids.index(default_id))


class StackComposer(QGroupBox):
    """9 dropdowns. Emits `selection_changed` whenever any choice changes."""

    selection_changed = Signal()

    def __init__(self, library: Library, parent: QWidget | None = None) -> None:
        super().__init__("Stack composition", parent)
        self._lib = library

        # ── component dropdowns ────────────────────────────────────────
        self._cb_membrane = QComboBox()
        _populate(self._cb_membrane, lf.membranes(library),
                  _DEFAULT_SELECTION_HINTS["membrane"])

        self._cb_anode_cl = QComboBox()
        _populate(self._cb_anode_cl, lf.anode_catalyst_layers(library),
                  _DEFAULT_SELECTION_HINTS["anode_cl"])

        self._cb_cathode_cl = QComboBox()
        _populate(self._cb_cathode_cl, lf.cathode_catalyst_layers(library),
                  _DEFAULT_SELECTION_HINTS["cathode_cl"])

        gdls = lf.gas_diffusion_layers(library)
        self._cb_anode_gdl = QComboBox()
        _populate(self._cb_anode_gdl, gdls, _DEFAULT_SELECTION_HINTS["anode_gdl"])
        self._cb_cathode_gdl = QComboBox()
        _populate(self._cb_cathode_gdl, gdls, _DEFAULT_SELECTION_HINTS["cathode_gdl"])

        bpps = lf.bipolar_plates(library)
        self._cb_anode_bpp = QComboBox()
        _populate(self._cb_anode_bpp, bpps, _DEFAULT_SELECTION_HINTS["anode_bpp"])
        self._cb_cathode_bpp = QComboBox()
        _populate(self._cb_cathode_bpp, bpps, _DEFAULT_SELECTION_HINTS["cathode_bpp"])

        # ── material dropdowns ─────────────────────────────────────────
        self._cb_membrane_material = QComboBox()
        _populate(self._cb_membrane_material, lf.membrane_materials(library),
                  _DEFAULT_SELECTION_HINTS["membrane_material"])

        self._cb_anode_cat_mat = QComboBox()
        _populate(self._cb_anode_cat_mat, lf.anode_catalyst_materials(library),
                  _DEFAULT_SELECTION_HINTS["anode_catalyst_material"])

        self._cb_cathode_cat_mat = QComboBox()
        _populate(self._cb_cathode_cat_mat, lf.cathode_catalyst_materials(library),
                  _DEFAULT_SELECTION_HINTS["cathode_catalyst_material"])

        # Wire all changes to the single signal.
        for cb in self._all_combos():
            cb.currentIndexChanged.connect(self._on_any_change)

        # ── layout ─────────────────────────────────────────────────────
        form = QFormLayout()
        form.addRow("Membrane", self._cb_membrane)
        form.addRow("  · material (ionomer)", self._cb_membrane_material)
        form.addRow("Anode catalyst layer", self._cb_anode_cl)
        form.addRow("  · material", self._cb_anode_cat_mat)
        form.addRow("Cathode catalyst layer", self._cb_cathode_cl)
        form.addRow("  · material", self._cb_cathode_cat_mat)
        form.addRow("Anode GDL", self._cb_anode_gdl)
        form.addRow("Cathode GDL", self._cb_cathode_gdl)
        form.addRow("Anode BPP", self._cb_anode_bpp)
        form.addRow("Cathode BPP", self._cb_cathode_bpp)

        outer = QFormLayout(self)
        outer.addRow(form)

    # ── public API ─────────────────────────────────────────────────────

    def current_selection(self) -> StackSelection:
        """Snapshot the current dropdowns into a `StackSelection`."""
        def _id(cb: QComboBox) -> str | None:
            data = cb.currentData()
            return str(data) if data is not None else None

        return StackSelection(
            membrane_id=_id(self._cb_membrane) or "",
            membrane_material_id=_id(self._cb_membrane_material) or "",
            anode_catalyst_material_id=_id(self._cb_anode_cat_mat) or "",
            cathode_catalyst_material_id=_id(self._cb_cathode_cat_mat) or "",
            anode_cl_id=_id(self._cb_anode_cl),
            cathode_cl_id=_id(self._cb_cathode_cl),
            anode_gdl_id=_id(self._cb_anode_gdl),
            cathode_gdl_id=_id(self._cb_cathode_gdl),
            anode_bpp_id=_id(self._cb_anode_bpp),
            cathode_bpp_id=_id(self._cb_cathode_bpp),
        )

    # ── internals ──────────────────────────────────────────────────────

    def _all_combos(self) -> list[QComboBox]:
        return [
            self._cb_membrane, self._cb_membrane_material,
            self._cb_anode_cl, self._cb_anode_cat_mat,
            self._cb_cathode_cl, self._cb_cathode_cat_mat,
            self._cb_anode_gdl, self._cb_cathode_gdl,
            self._cb_anode_bpp, self._cb_cathode_bpp,
        ]

    def _on_any_change(self) -> None:
        self.selection_changed.emit()
