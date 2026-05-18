"""OnboardingBanner — single dismissible hint for first-time users.

UX-VISION §8: shown once, dismissed on first slider-move or close-click,
remembered via `QSettings.ui.onboardingSeen`. No wizard, no splash.

Wraps a stylised `QFrame` with one line of copy and a close button. The
caller listens to `dismissed` (Signal) and persists the flag — this
widget itself stays Qt-only and has no QSettings dependency, so the
persistence layer can be tested independently.
"""

# ruff: noqa: I001
from __future__ import annotations

from . import qt_env  # noqa: F401

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)


_BANNER_TEXT = (
    "First session? Move any slider below — the V–I curve recomputes live. "
    "Each value cites its source (hover any dropdown)."
)


class OnboardingBanner(QFrame):
    """One-line tip banner that fades out on dismiss."""

    dismissed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("onboardingBanner")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "#onboardingBanner { background: #FFF8E1; "
            "border: 1px solid #F0CB7E; border-radius: 4px; }"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        label = QLabel(_BANNER_TEXT)
        label.setWordWrap(True)
        label.setStyleSheet("color: #5D4012;")

        close_btn = QPushButton("✕")
        close_btn.setFlat(True)
        close_btn.setFixedWidth(28)
        close_btn.setToolTip("Dismiss (Cmd+W)")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.dismiss)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.addWidget(label, stretch=1)
        layout.addWidget(close_btn)

    def dismiss(self) -> None:
        """Hide and emit `dismissed`. Safe to call multiple times."""
        if self.isVisible():
            self.setVisible(False)
            self.dismissed.emit()
