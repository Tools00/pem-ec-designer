"""CLI: generate library/schema.json from Pydantic models.

Run: `python -m pem_ec_designer.schema.cli` or `pem-ec-schema`.
CI checks that committed schema.json matches the regenerated one.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from .component import (
    AnodeCatalystLayer,
    BipolarPlate,
    CathodeCatalystLayer,
    Component,
    Endplate,
    FlowField,
    Gasket,
    GasDiffusionLayer,
    Membrane,
)
from .material import Material


def build_schema() -> dict:
    """Build a combined JSON Schema for all component subtypes + Material."""
    component_union = (
        Membrane
        | AnodeCatalystLayer
        | CathodeCatalystLayer
        | GasDiffusionLayer
        | BipolarPlate
        | FlowField
        | Endplate
        | Gasket
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "pem-ec-designer library schema",
        "description": "Generated from Pydantic. Do not edit by hand.",
        "$defs": {
            "Component":   TypeAdapter(component_union).json_schema(),
            "ComponentBase": Component.model_json_schema(),
            "Material":    Material.model_json_schema(),
        },
    }


def generate_schema_main() -> int:
    repo = Path(__file__).resolve().parents[3]
    out = repo / "library" / "schema.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    schema = build_schema()
    out.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out.relative_to(repo)} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(generate_schema_main())
