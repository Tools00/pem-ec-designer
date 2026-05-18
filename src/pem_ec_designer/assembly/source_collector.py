"""Collect BibTeX-source keys actually used by a given stack.

Walks the SourcedValue fields on the selected Components + Materials
and gathers the set of unique BibTeX keys (with the trailing locator
suffix stripped — `carmo2013ijhe.tab2` → `carmo2013ijhe`).

Used by the BibTeX-export feature: the resulting subset of
`library/sources.bib` ships next to a CSV/PDF as the "Strict-Quellen
receipt" for the design point.

Pure, no Qt. Doesn't load `sources.bib` — that is the export layer's job.
"""

from __future__ import annotations

from typing import Iterable

from ..schema.component import Component
from ..schema.material import Material
from ..schema.source import SourcedValue


_LOCATOR_KEYWORDS = ("tab", "fig", "eq", "sec", "p")


def _bibtex_key(source_id: str) -> str:
    """Strip locator suffix from a source-ID.

    Examples:
        `carmo2013ijhe.tab2`      → `carmo2013ijhe`
        `bernt2016jes.fig1a`      → `bernt2016jes`
        `chemours.datasheet.n117` → `chemours.datasheet.n117`  (datasheet key kept)

    Heuristic: the LAST dot-separated token is considered a locator iff
    it starts with a digit OR matches a locator-keyword (tab/fig/eq/sec/p)
    immediately followed by a digit. Anything else (e.g. `n117`, `axf5q`)
    is part of the BibTeX key itself.
    """
    parts = source_id.split(".")
    if len(parts) <= 1:
        return source_id
    last = parts[-1].lower()
    # Pure-digit-prefix locators (`.2`, `.10a`).
    if last and last[0].isdigit():
        return ".".join(parts[:-1])
    # Keyword + digit (`tab2`, `fig1a`, `eq3`).
    for kw in _LOCATOR_KEYWORDS:
        if last.startswith(kw) and len(last) > len(kw) and last[len(kw)].isdigit():
            return ".".join(parts[:-1])
    return source_id


def _walk_sourced_values(obj: object) -> Iterable[SourcedValue]:
    """Yield every SourcedValue attribute hanging off a Pydantic model."""
    if obj is None:
        return
    if hasattr(obj, "model_dump"):
        for name, val in obj.__dict__.items():  # type: ignore[attr-defined]
            if isinstance(val, SourcedValue):
                yield val
            elif hasattr(val, "model_dump") and val is not obj:
                # Nested model (e.g., CrossReference holds nothing relevant).
                # Avoid recursing into list/dict fields here — Library schema
                # keeps SourcedValues at one level for the relevant fields.
                pass


def collect_source_keys(
    components: Iterable[Component | None],
    materials: Iterable[Material | None],
) -> set[str]:
    """Set of unique BibTeX keys cited by the given components + materials."""
    keys: set[str] = set()
    for obj in list(components) + list(materials):
        for sv in _walk_sourced_values(obj):
            keys.add(_bibtex_key(sv.source))
    return keys
