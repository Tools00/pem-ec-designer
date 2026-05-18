"""Entry point: `python -m pem_ec_designer` opens the MainWindow.

Satisfies ADR-001 §Validation-Gate: opens MainWindow without crash.
"""

# ruff: noqa: I001  -- qt_env MUST precede PySide6 imports (see UI-LAUNCH-NOTES §1)
from __future__ import annotations

import sys
from pathlib import Path

from .ui import qt_env  # noqa: F401

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.persistence import APP_NAME, ORG_NAME


def main() -> int:
    # Set org/app name BEFORE constructing QApplication so QSettings
    # picks them up consistently across platforms.
    QCoreApplication.setOrganizationName(ORG_NAME)
    QCoreApplication.setApplicationName(APP_NAME)

    app = QApplication.instance() or QApplication(sys.argv)
    library_dir = Path(__file__).resolve().parent.parent.parent / "library"
    win = MainWindow(library_dir)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
