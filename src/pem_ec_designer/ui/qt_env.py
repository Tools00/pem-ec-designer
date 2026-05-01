"""Qt runtime environment fix-ups.

MUST be imported before any other PySide6 import. Sets QT_PLUGIN_PATH
so that anaconda/conda Python finds PySide6's bundled platform plugins
on macOS (see docs/UI-LAUNCH-NOTES.md §1).

Idempotent: safe to import multiple times.
"""

from __future__ import annotations

import os
from pathlib import Path

import PySide6


def configure() -> None:
    plugin_path = Path(PySide6.__file__).parent / "Qt" / "plugins"
    # Only set if user hasn't overridden — respect explicit user choice.
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugin_path))


configure()
