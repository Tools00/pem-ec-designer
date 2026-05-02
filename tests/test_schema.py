"""Pydantic schema tests."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from pem_ec_designer.schema import (
    CrossReference,
    GasDiffusionLayer,
    MaterialRef,
    Membrane,
    Quantity,
    SourcedValue,
)


def test_quantity_to_si() -> None:
    q = Quantity(value=183, unit="um")
    assert math.isclose(q.value_si, 1.83e-4, rel_tol=1e-12)


def test_quantity_to_other_unit() -> None:
    q = Quantity(value=183, unit="um")
    assert math.isclose(q.to("mm"), 0.183, rel_tol=1e-12)


def test_quantity_unknown_unit_rejected() -> None:
    with pytest.raises(ValidationError):
        Quantity(value=1.0, unit="furlong")


def test_sourced_value_requires_source() -> None:
    """Strict-Quellen (ADR-002 D4): no source → ValidationError."""
    with pytest.raises(ValidationError):
        SourcedValue[Quantity](value=Quantity(value=183, unit="um"), source="")


def test_sourced_value_with_source() -> None:
    sv = SourcedValue[Quantity](
        value=Quantity(value=183, unit="um"),
        source="chemours.datasheet.n117",
        confidence="datasheet",
    )
    assert sv.source == "chemours.datasheet.n117"
    assert sv.confidence == "datasheet"


def test_membrane_load() -> None:
    m = Membrane(
        id="membrane.nafion.117",
        name="Nafion 117 — 183 µm",
        material=MaterialRef(ref="nafion-1100"),
        thickness=SourcedValue[Quantity](
            value=Quantity(value=183, unit="um"),
            source="chemours.datasheet.n117",
        ),
    )
    assert m.id == "membrane.nafion.117"
    assert m.category == "membrane"
    assert math.isclose(m.thickness.value.value_si, 1.83e-4, rel_tol=1e-12)


def test_id_pattern_rejects_flat() -> None:
    """ADR-002 D5: hierarchical only, no flat slugs."""
    with pytest.raises(ValidationError):
        Membrane(
            id="nafion-117",  # flat, no dot
            name="Nafion 117",
            material=MaterialRef(ref="nafion-1100"),
            thickness=SourcedValue[Quantity](
                value=Quantity(value=183, unit="um"),
                source="chemours.datasheet.n117",
            ),
        )


def test_id_pattern_accepts_hierarchical() -> None:
    m = Membrane(
        id="membrane.nafion.117",
        name="N",
        material=MaterialRef(ref="nafion-1100"),
        thickness=SourcedValue[Quantity](
            value=Quantity(value=1, unit="um"),
            source="dummy.testkey",
        ),
    )
    assert m.id == "membrane.nafion.117"


# ─── GDL + CrossReference (added with E1 schema extension) ──────────


def _q(v: float, u: str) -> Quantity:
    return Quantity(value=v, unit=u)


def _sv(v: float, u: str, src: str = "toray.datasheet.tgph") -> SourcedValue[Quantity]:
    return SourcedValue[Quantity](value=_q(v, u), source=src, confidence="datasheet")


def test_gdl_minimal_no_material() -> None:
    """Composite components (GDL bilayer) may omit `material`."""
    gdl = GasDiffusionLayer(
        id="gdl.toray.tgph060",
        name="Toray TGP-H-060",
        manufacturer="Toray Industries, Inc.",
        thickness=_sv(190, "um"),
        has_mpl=False,
    )
    assert gdl.material is None
    assert gdl.has_mpl is False
    assert gdl.cross_references == []


def test_gdl_full_payload() -> None:
    """All E1 fields validate and round-trip to SI."""
    gdl = GasDiffusionLayer(
        id="gdl.toray.tgph060",
        name="Toray TGP-H-060",
        manufacturer="Toray Industries, Inc.",
        thickness=_sv(190, "um"),
        porosity=_sv(78, "percent"),
        bulk_density=_sv(0.44, "g/cm^3"),
        electrical_resistivity_through_plane=_sv(80, "mohm·cm"),
        thermal_conductivity_through_plane=_sv(1.7, "W/(m·K)"),
        cross_references=[
            CrossReference(source="aquah2024scirep", note="μCT porosity 0.84")
        ],
    )
    assert math.isclose(gdl.porosity.value.value_si, 0.78, rel_tol=1e-12)
    assert math.isclose(gdl.bulk_density.value.value_si, 440.0, rel_tol=1e-12)
    assert len(gdl.cross_references) == 1
    assert gdl.cross_references[0].source == "aquah2024scirep"


def test_cross_reference_requires_source() -> None:
    """CrossReference.source is required and non-empty (Strict-Quellen)."""
    with pytest.raises(ValidationError):
        CrossReference(source="", note="x")
    with pytest.raises(ValidationError):
        CrossReference()  # type: ignore[call-arg]


def test_component_extra_field_still_forbidden() -> None:
    """E1 added fields, but extra='forbid' must still reject unknowns."""
    with pytest.raises(ValidationError):
        GasDiffusionLayer(
            id="gdl.toray.tgph060",
            name="x",
            thickness=_sv(190, "um"),
            mystery_field=42,  # type: ignore[call-arg]
        )
