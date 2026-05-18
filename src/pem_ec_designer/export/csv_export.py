"""CSV export — V–I-curve + loss breakdown with self-documenting header.

Format (UX-VISION §10):
    # pem-ec-designer — polarisation curve export
    # generated: 2026-05-17T04:20:00
    # T = 80 °C, p_H2 = 1 bar, p_O2 = 1 bar
    # stack: membrane=..., anode_cl=..., ...
    # sources cited: bernt2016jes, carmo2013ijhe, ...
    j_A_cm2, V_cell, E_rev, eta_OER, eta_HER, eta_ohm
    ...

Header is comment-prefixed so spreadsheet apps treat it as metadata.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Iterable

from ..physics.polarization import PolarisationCurve


@dataclass(frozen=True)
class CSVExportMetadata:
    """Caller-provided context to render the comment header."""

    T_celsius: float
    p_h2_bar: float
    p_o2_bar: float
    stack_components: dict[str, str | None]   # role → component-id
    stack_materials: dict[str, str | None]    # role → material-id
    sources_cited: Iterable[str]              # BibTeX keys (already deduped)
    design_j_A_per_cm2: float | None = None


def render_polarisation_csv(curve: PolarisationCurve, meta: CSVExportMetadata) -> str:
    """Render the export as a single string (testable without disk-IO)."""
    if not curve.points:
        raise ValueError("Cannot export an empty PolarisationCurve")

    buf = StringIO()
    buf.write("# pem-ec-designer — polarisation curve export\n")
    buf.write(f"# generated: {datetime.now().isoformat(timespec='seconds')}\n")
    buf.write(
        f"# operating-point: T = {meta.T_celsius:.1f} °C, "
        f"p_H2 = {meta.p_h2_bar:.1f} bar, p_O2 = {meta.p_o2_bar:.1f} bar\n"
    )
    if meta.design_j_A_per_cm2 is not None:
        buf.write(f"# design_j = {meta.design_j_A_per_cm2:.2f} A/cm²\n")
    for role, cid in meta.stack_components.items():
        if cid:
            buf.write(f"# stack.{role}: {cid}\n")
    for role, mid in meta.stack_materials.items():
        if mid:
            buf.write(f"# material.{role}: {mid}\n")
    sources = sorted(set(meta.sources_cited))
    if sources:
        buf.write(f"# sources_cited: {', '.join(sources)}\n")
    buf.write("# units: j in A/cm², voltages in V\n")

    writer = csv.writer(buf)
    writer.writerow(["j_A_cm2", "V_cell", "E_rev", "eta_OER", "eta_HER", "eta_ohm"])
    for p in curve.points:
        writer.writerow([
            f"{p.j / 1e4:.6g}",
            f"{p.v_cell:.6g}",
            f"{p.e_rev:.6g}",
            f"{p.eta_oer:.6g}",
            f"{p.eta_her:.6g}",
            f"{p.eta_ohm:.6g}",
        ])
    return buf.getvalue()


def write_polarisation_csv(
    curve: PolarisationCurve, meta: CSVExportMetadata, path: Path
) -> None:
    """Write the CSV to `path` (creates parents if needed)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_polarisation_csv(curve, meta), encoding="utf-8")
