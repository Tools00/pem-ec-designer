"""Smoke-test the MainWindow without manual interaction.

Opens the window, lets the auto-selected first component render, takes
a screenshot, exits. Used both as a manual sanity check and as
evidence that ADR-001's launch gate ('opens MainWindow without crash')
holds after every change.
"""

# ruff: noqa: I001  -- qt_env MUST precede PySide6 imports (see UI-LAUNCH-NOTES §1)
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from pem_ec_designer.ui import qt_env  # noqa: F401

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pem_ec_designer.ui.main_window import MainWindow


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    library_dir = Path(__file__).resolve().parents[1] / "library"
    win = MainWindow(library_dir)
    win.show()
    app.processEvents()
    win._plotter.render()  # type: ignore[attr-defined]
    app.processEvents()

    out = Path(tempfile.gettempdir()) / "pem_ec_designer_mainwindow.png"
    win._plotter.screenshot(str(out))  # type: ignore[attr-defined]

    if not out.exists() or out.stat().st_size < 1000:
        print(f"[FAIL] screenshot empty: {out}", file=sys.stderr)
        return 2

    print(f"[ok] mainwindow screenshot {out} ({out.stat().st_size} bytes)")

    QTimer.singleShot(0, app.quit)
    app.exec()
    return 0


if __name__ == "__main__":
    sys.exit(main())
