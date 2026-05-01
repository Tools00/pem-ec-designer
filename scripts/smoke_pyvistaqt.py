"""pyvistaqt + PySide6 smoke test (macOS arm64 / VTK / OpenGL).

Goal: prove the UI render pipeline works end-to-end on this machine
BEFORE writing any UI code. If this script crashes or hangs, the
unknown CAD-stack risk has surfaced cheaply.

Pipeline exercised:
  1. PySide6 QApplication starts.
  2. pyvistaqt.QtInteractor embeds a VTK render window in a Qt widget.
  3. A build123d Part (membrane spec → STL) is loaded into pyvista.
  4. Render is triggered off-screen, screenshot saved.
  5. App quits cleanly (no event loop).

Run:  python scripts/smoke_pyvistaqt.py
Exit: 0 = green pipeline, !=0 = something is broken — read traceback.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from build123d import export_stl
from PySide6.QtWidgets import QApplication, QMainWindow
from pyvistaqt import QtInteractor

import pyvista as pv
from pem_ec_designer.geometry import build_membrane
from pem_ec_designer.materials import load_library


def main() -> int:
    # 1. Qt
    app = QApplication.instance() or QApplication(sys.argv)

    # 2. Build geometry from real spec
    lib = load_library(Path(__file__).resolve().parents[1] / "library")
    spec = lib.components["membrane.nafion.117"]
    part = build_membrane(spec)  # type: ignore[arg-type]

    # 3. build123d Part -> STL -> pyvista mesh (the standard bridge)
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        stl_path = Path(tmp.name)
    export_stl(part, str(stl_path))
    mesh = pv.read(stl_path)
    print(f"[ok] mesh loaded: {mesh.n_points} points, {mesh.n_cells} cells")

    # 4. Embed QtInteractor in a MainWindow. show() is required so that
    #    the underlying VTK render window is created before screenshot().
    win = QMainWindow()
    plotter = QtInteractor(win)
    win.setCentralWidget(plotter.interactor)
    plotter.add_mesh(mesh, color="cornflowerblue", show_edges=False)
    plotter.reset_camera()
    win.show()
    app.processEvents()
    plotter.render()
    app.processEvents()

    # 5. Screenshot
    out = Path(tempfile.gettempdir()) / "pem_ec_designer_smoke.png"
    plotter.screenshot(str(out))
    plotter.close()
    win.close()

    if not out.exists() or out.stat().st_size < 1000:
        print(f"[FAIL] screenshot not written or empty: {out}", file=sys.stderr)
        return 2
    print(f"[ok] screenshot {out} ({out.stat().st_size} bytes)")

    app.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
