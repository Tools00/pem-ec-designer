"""Tests for export/ — CSV + BibTeX subset writers."""

from __future__ import annotations

from pathlib import Path

import pytest

from pem_ec_designer.export.bibtex_export import (
    render_bibtex_subset,
    split_bibtex_entries,
    write_bibtex_subset,
)
from pem_ec_designer.export.csv_export import (
    CSVExportMetadata,
    render_polarisation_csv,
    write_polarisation_csv,
)
from pem_ec_designer.physics.ohmic import OhmicContribution
from pem_ec_designer.physics.polarization import (
    CellKinetics,
    OperatingPoint,
    polarisation_curve,
)


# ── fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def small_curve():
    j_values = [1e3, 1e4, 2e4, 3e4]  # 0.1 – 3 A/cm²
    return polarisation_curve(
        j_values=j_values,
        kinetics=CellKinetics(j0_anode=1e-2, alpha_anode=0.5,
                              j0_cathode=1.0, alpha_cathode=0.5),
        op=OperatingPoint(T=353.15, p_h2=1e5, p_o2=1e5),
        ohmic=[OhmicContribution(label="m", asr=5e-6)],
    )


@pytest.fixture
def csv_meta():
    return CSVExportMetadata(
        T_celsius=80.0,
        p_h2_bar=1.0,
        p_o2_bar=1.0,
        stack_components={"membrane": "membrane.nafion.212"},
        stack_materials={"anode_cat": "iro2-tio2-catalyst"},
        sources_cited={"bernt2016jes", "carmo2013ijhe", "kusoglu2017chemrev"},
        design_j_A_per_cm2=1.0,
    )


# ── CSV ───────────────────────────────────────────────────────────────


def test_csv_header_contains_metadata(small_curve, csv_meta) -> None:
    out = render_polarisation_csv(small_curve, csv_meta)
    assert "# pem-ec-designer" in out
    assert "T = 80.0 °C" in out
    assert "membrane.nafion.212" in out
    assert "iro2-tio2-catalyst" in out
    assert "bernt2016jes" in out
    assert "design_j = 1.00 A/cm²" in out


def test_csv_row_count_matches_curve(small_curve, csv_meta) -> None:
    out = render_polarisation_csv(small_curve, csv_meta)
    rows = [ln for ln in out.splitlines() if ln and not ln.startswith("#")]
    # 1 header + 4 data rows
    assert len(rows) == 5
    assert rows[0].startswith("j_A_cm2")


def test_csv_units_explicit(small_curve, csv_meta) -> None:
    out = render_polarisation_csv(small_curve, csv_meta)
    assert "units: j in A/cm²" in out


def test_csv_rejects_empty_curve(csv_meta) -> None:
    from pem_ec_designer.physics.polarization import PolarisationCurve
    with pytest.raises(ValueError):
        render_polarisation_csv(PolarisationCurve(points=[]), csv_meta)


def test_csv_writes_to_disk(small_curve, csv_meta, tmp_path) -> None:
    out_path = tmp_path / "subdir" / "run.csv"
    write_polarisation_csv(small_curve, csv_meta, out_path)
    assert out_path.exists()
    assert out_path.read_text().startswith("# pem-ec-designer")


# ── BibTeX subset ─────────────────────────────────────────────────────


def test_split_bibtex_entries_finds_real_keys() -> None:
    text = Path("library/sources.bib").read_text()
    entries = split_bibtex_entries(text)
    assert "bernt2016jes" in entries
    assert "carmo2013ijhe" in entries
    assert "schmidt2017ijhe" in entries
    # Datasheet keys with dotted IDs survive intact.
    assert "chemours.datasheet.n117" in entries


def test_split_bibtex_entries_blocks_are_well_formed() -> None:
    text = Path("library/sources.bib").read_text()
    entries = split_bibtex_entries(text)
    for key, block in entries.items():
        assert block.startswith("@"), f"{key} block doesn't start with @"
        assert block.rstrip().endswith("}"), f"{key} block isn't brace-closed"


def test_render_bibtex_subset_keeps_only_requested() -> None:
    text = Path("library/sources.bib").read_text()
    out = render_bibtex_subset(text, {"bernt2016jes", "schmidt2017ijhe"})
    assert "bernt2016jes" in out
    assert "schmidt2017ijhe" in out
    assert "carmo2013ijhe" not in out
    # Header summary present
    assert "Subset of library/sources.bib" in out
    assert "2 of 2 requested entries found" in out


def test_render_bibtex_subset_handles_missing_key() -> None:
    text = Path("library/sources.bib").read_text()
    out = render_bibtex_subset(text, {"nonexistent2099"})
    assert "0 of 1 requested entries found" in out


def test_write_bibtex_subset_returns_found_keys(tmp_path) -> None:
    out_path = tmp_path / "cited.bib"
    found = write_bibtex_subset(
        Path("library/sources.bib"),
        {"bernt2016jes", "schmidt2017ijhe", "nonexistent2099"},
        out_path,
    )
    assert found == {"bernt2016jes", "schmidt2017ijhe"}
    assert out_path.exists()


def test_export_modules_no_qt_imports() -> None:
    import pem_ec_designer.export.bibtex_export as a
    import pem_ec_designer.export.csv_export as b
    for mod in (a, b):
        assert "PySide6" not in Path(mod.__file__).read_text()
