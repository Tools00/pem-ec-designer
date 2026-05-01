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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QSplitter,
)
from pyvistaqt import QtInteractor

from ..geometry import build_extruded
from ..materials import load_library
from ..schema import Component
from .viewer import part_to_mesh


class MainWindow(QMainWindow):
    def __init__(self, library_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("pem-ec-designer v0")
        self.resize(1100, 700)

        self._lib = load_library(library_dir)

        self._list = QListWidget()
        for cid in sorted(self._lib.components):
            item = QListWidgetItem(cid)
            item.setData(Qt.ItemDataRole.UserRole, cid)
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_selection)

        self._plotter = QtInteractor(self)
        self._plotter.set_background("white")
        self._plotter.add_axes()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._list)
        splitter.addWidget(self._plotter.interactor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 840])
        self.setCentralWidget(splitter)

        self.statusBar().showMessage(
            f"Library loaded: {len(self._lib.components)} components, "
            f"{len(self._lib.materials)} materials."
        )

        # Auto-select first item so the viewer is never empty on launch.
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

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
        self._plotter.clear()
        self._plotter.add_mesh(mesh, color="cornflowerblue", show_edges=True)
        self._plotter.reset_camera()
        self._plotter.render()

        thickness_mm = component.thickness.value.value_si * 1000.0
        self.statusBar().showMessage(
            f"{cid}  ·  {component.name}  ·  thickness {thickness_mm:.3f} mm  "
            f"·  source {component.thickness.source}"
        )
