"""build123d Part -> pyvista mesh bridge.

Standard route: tessellate via build123d STL export, load with pyvista.
Lives here (not in geometry/) because it depends on pyvista, which is
a UI-layer concern.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pyvista as pv
from build123d import Part, export_stl


def part_to_mesh(part: Part) -> pv.PolyData:
    """Tessellate a build123d Part into a pyvista mesh via STL."""
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        export_stl(part, str(path))
        return pv.read(path)
    finally:
        path.unlink(missing_ok=True)
