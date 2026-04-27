"""Pydantic schema tests."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from pem_ec_designer.schema import (
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
