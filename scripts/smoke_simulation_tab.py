"""Smoke-test the Simulation tab — opens MainWindow, switches to the
Simulation tab, grabs the central widget, saves a PNG. Used as evidence
that the Matplotlib + operating-condition pipeline runs end-to-end.
"""

# ruff: noqa: I001
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from pem_ec_designer.ui import qt_env  # noqa: F401

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QTabWidget

from pem_ec_designer.ui.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    library_dir = Path(__file__).resolve().parents[1] / "library"
    win = MainWindow(library_dir)
    win.resize(1300, 800)
    win.show()
    app.processEvents()

    # Switch to the Simulation tab (index 1).
    tabs = win.centralWidget()
    assert isinstance(tabs, QTabWidget), "centralWidget is no longer a QTabWidget"
    tabs.setCurrentIndex(1)
    app.processEvents()

    # Trigger one extra recompute so the layout has settled.
    win._recompute_polarisation()  # type: ignore[attr-defined]
    app.processEvents()

    out = Path(tempfile.gettempdir()) / "pem_ec_designer_simulation.png"
    pixmap = win.grab()
    if not pixmap.save(str(out), "PNG"):
        print(f"[FAIL] grab().save returned False for {out}", file=sys.stderr)
        return 2

    if not out.exists() or out.stat().st_size < 5_000:
        print(f"[FAIL] screenshot too small: {out}", file=sys.stderr)
        return 2

    print(f"[ok] simulation-tab screenshot {out} ({out.stat().st_size} bytes)")

    QTimer.singleShot(0, app.quit)
    app.exec()
    return 0


if __name__ == "__main__":
    sys.exit(main())
