"""Stack-geometry aggregation for STEP export — see ADR-008.

Pure (no Qt). Takes resolved Library `Component`s in fixed PEM-EC order
(anode side → membrane → cathode side), extrudes each by its own
footprint+thickness, stacks them on the Z-axis at true SI dimensions,
and returns a build123d `Compound` plus a sidecar-ready layer manifest.

Layer order is hardcoded (ADR-006: geometry of the cell is fixed).
Any layer without a footprint is skipped and reported.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from build123d import Compound, Pos

from ..schema.component import Component
from .extruded import build_extruded

_M_TO_MM = 1000.0

LAYER_ORDER: tuple[str, ...] = (
    "anode_bpp",
    "anode_gdl",
    "anode_cl",
    "membrane",
    "cathode_cl",
    "cathode_gdl",
    "cathode_bpp",
)


@dataclass(frozen=True)
class LayerPlacement:
    role: str
    component_id: str
    thickness_mm: float
    z_start_mm: float
    z_end_mm: float
    material_id: str | None
    footprint: dict  # serialisable form, for sidecar JSON


@dataclass
class StackAssembly:
    compound: Compound
    layers: list[LayerPlacement] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _footprint_dict(comp: Component) -> dict:
    fp = comp.footprint
    if fp is None:
        return {}
    if fp.shape == "circular":
        return {"shape": "circular",
                "diameter_mm": fp.diameter.value_si * _M_TO_MM}
    return {"shape": fp.shape,
            "width_mm": fp.width.value_si * _M_TO_MM if fp.width else None,
            "height_mm": fp.height.value_si * _M_TO_MM if fp.height else None}


def build_stack_assembly(
    *,
    anode_bpp: Component | None = None,
    anode_gdl: Component | None = None,
    anode_cl: Component | None = None,
    membrane: Component | None = None,
    cathode_cl: Component | None = None,
    cathode_gdl: Component | None = None,
    cathode_bpp: Component | None = None,
) -> StackAssembly:
    """Build a stacked Compound from selected layers in fixed PEM order.

    Each layer extrudes its own footprint at true thickness. Layers
    missing entirely (None) or missing a footprint are recorded in
    `skipped` and excluded from the Compound.
    """
    by_role: dict[str, Component | None] = {
        "anode_bpp": anode_bpp,
        "anode_gdl": anode_gdl,
        "anode_cl": anode_cl,
        "membrane": membrane,
        "cathode_cl": cathode_cl,
        "cathode_gdl": cathode_gdl,
        "cathode_bpp": cathode_bpp,
    }

    placements: list[LayerPlacement] = []
    skipped: list[str] = []
    parts = []
    z_cursor_mm = 0.0

    for role in LAYER_ORDER:
        comp = by_role[role]
        if comp is None:
            skipped.append(f"{role} — not selected")
            continue
        if comp.footprint is None:
            skipped.append(f"{role}:{comp.id} — no footprint in library")
            continue
        try:
            part = build_extruded(comp)
        except ValueError as exc:
            skipped.append(f"{role}:{comp.id} — {exc}")
            continue

        thickness_mm = comp.thickness.value.value_si * _M_TO_MM
        z_start = z_cursor_mm
        z_end = z_cursor_mm + thickness_mm
        # build123d primitives are centered at origin → translate to slab center.
        translated = Pos(0, 0, z_start + thickness_mm / 2.0) * part
        parts.append(translated)

        placements.append(
            LayerPlacement(
                role=role,
                component_id=comp.id,
                thickness_mm=thickness_mm,
                z_start_mm=z_start,
                z_end_mm=z_end,
                material_id=comp.material.ref if comp.material is not None else None,
                footprint=_footprint_dict(comp),
            )
        )
        z_cursor_mm = z_end

    compound = Compound(label="pem_ec_stack", children=parts)
    return StackAssembly(compound=compound, layers=placements, skipped=skipped)


def assembly_to_sidecar(
    assembly: StackAssembly,
    *,
    app_version: str,
    operating_point: dict | None = None,
) -> dict:
    """Render a `StackAssembly` into the JSON-sidecar shape (ADR-008 §D5)."""
    return {
        "stack": f"PEM-EC single cell (pem-ec-designer {app_version})",
        "operating_point": operating_point or {},
        "layers": [
            {
                "index": i,
                "role": p.role,
                "id": p.component_id,
                "material": p.material_id,
                "thickness_mm": p.thickness_mm,
                "footprint": p.footprint,
                "z_start_mm": p.z_start_mm,
                "z_end_mm": p.z_end_mm,
            }
            for i, p in enumerate(assembly.layers)
        ],
        "skipped": assembly.skipped,
    }
