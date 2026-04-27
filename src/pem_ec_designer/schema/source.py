"""SourcedValue = a value + reference ID into BibTeX.

ADR-002 D4: every numerical value carries a source-ID. Library
loader cross-checks IDs against `library/sources.bib`.

Source-ID format (convention):
    {key}.{locator?}
e.g.
    carmo2013ijhe.tab2     → BibTeX key 'carmo2013ijhe', Table 2
    chemours.datasheet.n117 → BibTeX key 'chemours.datasheet.n117'
    bernt2018jes.fig1a     → BibTeX key 'bernt2018jes', Figure 1a

Confidence is implicitly 'paper' if the BibTeX key resolves;
estimates / TODO go through `confidence='estimate'` and source MUST
still resolve to a non-empty BibTeX key (e.g. 'internal.estimate.YYYY').
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


SourceId = str  # type alias — validated separately by load_library()


class SourcedValue(BaseModel, Generic[T]):
    """A value with a reference into the BibTeX source database.

    Per ADR-002 D4 (Strict-Quellen): `source` is REQUIRED. Pydantic
    refuses to construct a SourcedValue without it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: T
    source: SourceId = Field(..., min_length=3, description="BibTeX-key reference")
    confidence: Literal["paper", "datasheet", "estimate", "guess"] = Field(
        default="paper",
        description="Quality of the source. 'estimate'/'guess' must still cite a key.",
    )
    note: str | None = Field(default=None, description="Free-text qualifier")

    @field_validator("source")
    @classmethod
    def _no_empty_source(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source must be non-empty (Strict-Quellen-Pflicht, ADR-002)")
        return v.strip()

    def __repr__(self) -> str:
        return f"SourcedValue({self.value!r} @ {self.source})"
