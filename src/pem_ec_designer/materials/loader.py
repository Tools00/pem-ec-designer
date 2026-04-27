"""Library loading + cross-validation.

Loads:
- library/materials.json    → dict[str, Material]
- library/components/*.json → dict[id, Component subclass]
- library/sources.bib       → set[str] of BibTeX keys

Cross-checks:
- Every Component.material.ref must exist in materials
- Every SourcedValue.source must exist in sources.bib (Strict-Quellen)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..schema import (
    AnodeCatalystLayer,
    BipolarPlate,
    CathodeCatalystLayer,
    Component,
    Endplate,
    FlowField,
    GasDiffusionLayer,
    Gasket,
    Material,
    Membrane,
)

# Map JSON file basename → component class
_CATEGORY_CLASSES: dict[str, type[Component]] = {
    "membrane":    Membrane,
    "anode_cl":    AnodeCatalystLayer,
    "cathode_cl":  CathodeCatalystLayer,
    "gdl":         GasDiffusionLayer,
    "bpp":         BipolarPlate,
    "flow_field":  FlowField,
    "endplate":    Endplate,
    "gasket":      Gasket,
}


class LibraryLoadError(ValueError):
    """Raised when library load or cross-validation fails."""


@dataclass
class Library:
    materials: dict[str, Material] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)
    sources: set[str] = field(default_factory=set)

    def get_component(self, component_id: str) -> Component:
        if component_id not in self.components:
            raise KeyError(f"unknown component id: {component_id!r}")
        return self.components[component_id]

    def get_material(self, material_id: str) -> Material:
        if material_id not in self.materials:
            raise KeyError(f"unknown material id: {material_id!r}")
        return self.materials[material_id]


# ─── BibTeX parser ───────────────────────────────────────────────────

_BIBTEX_KEY = re.compile(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)


def _parse_bibtex_keys(bib_text: str) -> set[str]:
    """Extract just the @entry{key, ...} keys. We don't need full parsing."""
    return set(_BIBTEX_KEY.findall(bib_text))


# ─── Source-ID resolution ────────────────────────────────────────────

def _source_resolves(source_id: str, bib_keys: set[str]) -> bool:
    """A source-ID like 'carmo2013ijhe.tab2' resolves if a BibTeX key
    matches a prefix of the dotted parts (greedy left-to-right)."""
    parts = source_id.split(".")
    for i in range(len(parts), 0, -1):
        candidate = ".".join(parts[:i])
        if candidate in bib_keys:
            return True
    return False


def _walk_source_ids(obj: Any) -> list[str]:
    """Collect every value of a 'source' field in a nested dict/model."""
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "source" and isinstance(v, str):
                found.append(v)
            else:
                found.extend(_walk_source_ids(v))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_walk_source_ids(item))
    elif hasattr(obj, "model_dump"):
        found.extend(_walk_source_ids(obj.model_dump()))
    return found


# ─── Main loader ─────────────────────────────────────────────────────

def load_library(library_dir: str | Path) -> Library:
    """Load and cross-validate the entire library."""
    root = Path(library_dir).resolve()
    if not root.is_dir():
        raise LibraryLoadError(f"library dir not found: {root}")

    lib = Library()

    # 1. Sources
    bib_path = root / "sources.bib"
    if bib_path.is_file():
        lib.sources = _parse_bibtex_keys(bib_path.read_text(encoding="utf-8"))
    else:
        raise LibraryLoadError(f"missing {bib_path} (Strict-Quellen-Pflicht)")

    # 2. Materials
    mat_path = root / "materials.json"
    if mat_path.is_file():
        raw = json.loads(mat_path.read_text(encoding="utf-8"))
        for mat_id, mat_data in raw.items():
            try:
                lib.materials[mat_id] = Material.model_validate(mat_data)
            except ValidationError as e:
                raise LibraryLoadError(
                    f"material {mat_id!r} failed validation: {e}"
                ) from e
    # 3. Components per category
    comp_dir = root / "components"
    if comp_dir.is_dir():
        for json_file in sorted(comp_dir.glob("*.json")):
            category = json_file.stem
            cls = _CATEGORY_CLASSES.get(category)
            if cls is None:
                raise LibraryLoadError(
                    f"unknown component category file: {json_file.name}"
                )
            raw = json.loads(json_file.read_text(encoding="utf-8"))
            for comp_id, comp_data in raw.items():
                # ID is the dict key; ensure the inner record has it too
                comp_data.setdefault("id", comp_id)
                try:
                    component = cls.model_validate(comp_data)
                except ValidationError as e:
                    raise LibraryLoadError(
                        f"component {comp_id!r} failed validation: {e}"
                    ) from e
                lib.components[component.id] = component

    # 4. Cross-validation
    _cross_validate(lib)
    return lib


def _cross_validate(lib: Library) -> None:
    errors: list[str] = []

    for cid, comp in lib.components.items():
        # Material ref must exist
        ref_id = comp.material.ref
        if ref_id not in lib.materials:
            errors.append(f"component {cid}: unknown material ref {ref_id!r}")

        # Every source-id must resolve into BibTeX keys
        for source_id in _walk_source_ids(comp):
            if not _source_resolves(source_id, lib.sources):
                errors.append(
                    f"component {cid}: source {source_id!r} not found in sources.bib"
                )

    for mid, mat in lib.materials.items():
        for source_id in _walk_source_ids(mat):
            if not _source_resolves(source_id, lib.sources):
                errors.append(
                    f"material {mid}: source {source_id!r} not found in sources.bib"
                )

    if errors:
        raise LibraryLoadError(
            "Library cross-validation failed (Strict-Quellen, ADR-002 D4):\n  "
            + "\n  ".join(errors)
        )
