"""Stack assembly — bridge from Library Components/Materials to physics inputs.

This is the layer that lets the UI build a `CellKinetics` +
`list[OhmicContribution]` + `OperatingPoint` from a chosen set of
Library entries, so `physics.polarization.cell_voltage` can run on them.

Design choices:
  - Pure functions, no UI dependencies (UI imports from here, not the
    other way around). Layer-trennung per ADR-001 §3.1.
  - Strict-quellen propagated: an Ohmic contribution is built ONLY if
    the underlying Component has a citable ASR or (thickness + σ);
    otherwise it is silently skipped and the caller can see in the
    returned list which layers contributed and which didn't.
  - Per ADR-004 §Out-of-scope: ionic resistance through CL bulk is
    folded into the CL component's `area_specific_resistance_through_plane`
    (when known) — no separate ionomer/electrolyte model here.

Conceptual stack assumed (single cell):

    [Anode BPP] — [Anode GDL] — [Anode CL] — [Membrane] — [Cathode CL] — [Cathode GDL] — [Cathode BPP]

Each layer contributes one OhmicContribution (or zero, if not
parameterised).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..physics.ohmic import OhmicContribution, asr_from_thickness_and_conductivity
from ..physics.polarization import CellKinetics, OperatingPoint
from ..schema.component import (
    BipolarPlate,
    CathodeCatalystLayer,
    Component,
    GasDiffusionLayer,
    Membrane,
)
from ..schema.material import Material


@dataclass
class StackBuild:
    """Result of bridging a chosen stack into physics inputs."""

    kinetics: CellKinetics
    operating_point: OperatingPoint
    ohmic: list[OhmicContribution]
    skipped_layers: list[str]   # human-readable reasons (for UI diagnostics)


def _asr_from_component(label: str, comp: Component) -> OhmicContribution | None:
    """Try to pull a usable through-plane ASR from a Component.

    Order of preference:
    1. Direct `area_specific_resistance_through_plane` field.
    2. Compute ASR = thickness / σ from `electrical_resistivity_through_plane`.
    3. None → skip with reason.
    """
    asr_field = getattr(comp, "area_specific_resistance_through_plane", None)
    if asr_field is not None:
        return OhmicContribution(label=label, asr=asr_field.value.value_si)

    rho_field = getattr(comp, "electrical_resistivity_through_plane", None)
    thickness = comp.thickness.value.value_si  # m
    if rho_field is not None:
        rho_si = rho_field.value.value_si  # Ω·m
        # ASR [Ω·m²] = ρ [Ω·m] × thickness [m]
        return OhmicContribution(label=label, asr=rho_si * thickness)

    return None


def _membrane_asr(membrane: Membrane, membrane_material: Material) -> OhmicContribution | None:
    """Membrane ASR = thickness / σ. Both come from the Material spec."""
    if membrane_material.sigma_S_per_m is None:
        return None
    sigma = membrane_material.sigma_S_per_m.value.value_si
    thickness = membrane.thickness.value.value_si
    asr = asr_from_thickness_and_conductivity(thickness, sigma)
    return OhmicContribution(label=f"membrane:{membrane.id}", asr=asr)


def _kinetics_from_catalysts(
    anode_material: Material,
    cathode_material: Material,
) -> CellKinetics:
    """Pull j0 + α for each electrode from its catalyst Material.

    Raises:
        ValueError: a required kinetic field is missing on either material.
    """
    missing: list[str] = []
    for field, mat in [
        ("j0_anode", anode_material),
        ("alpha_anode", anode_material),
        ("j0_cathode", cathode_material),
        ("alpha_cathode", cathode_material),
    ]:
        if getattr(mat, field, None) is None:
            missing.append(f"{mat.name}.{field}")
    if missing:
        raise ValueError(
            "Catalyst material(s) missing kinetic fields: "
            + ", ".join(missing)
            + ". Populate them in library/materials.json (see iro2-tio2-catalyst for example)."
        )

    return CellKinetics(
        j0_anode=anode_material.j0_anode.value.value_si,
        alpha_anode=anode_material.alpha_anode.value.value_si,
        j0_cathode=cathode_material.j0_cathode.value.value_si,
        alpha_cathode=cathode_material.alpha_cathode.value.value_si,
    )


def build_stack(
    *,
    membrane: Membrane,
    membrane_material: Material,
    anode_catalyst_material: Material,
    cathode_catalyst_material: Material,
    anode_cl: Component | None = None,
    cathode_cl: CathodeCatalystLayer | None = None,
    anode_gdl: GasDiffusionLayer | None = None,
    cathode_gdl: GasDiffusionLayer | None = None,
    anode_bpp: BipolarPlate | None = None,
    cathode_bpp: BipolarPlate | None = None,
    T: float = 353.15,
    p_h2: float = 1e5,
    p_o2: float = 1e5,
) -> StackBuild:
    """Compose a single-cell stack from Library entries.

    Only `membrane`, `membrane_material`, and the two catalyst Materials
    are required. CL/GDL/BPP components are optional — any layer whose
    ASR cannot be determined (no datasheet ASR and no resistivity field)
    is skipped and reported in `skipped_layers`.
    """
    kinetics = _kinetics_from_catalysts(anode_catalyst_material, cathode_catalyst_material)
    op = OperatingPoint(T=T, p_h2=p_h2, p_o2=p_o2)

    ohmic: list[OhmicContribution] = []
    skipped: list[str] = []

    # Membrane (required, but σ might still be missing).
    mem_contrib = _membrane_asr(membrane, membrane_material)
    if mem_contrib is None:
        skipped.append(
            f"membrane:{membrane.id} — material '{membrane_material.name}' has no sigma_S_per_m"
        )
    else:
        ohmic.append(mem_contrib)

    # Other layers (all optional).
    for label_prefix, comp in [
        ("anode_cl", anode_cl),
        ("cathode_cl", cathode_cl),
        ("anode_gdl", anode_gdl),
        ("cathode_gdl", cathode_gdl),
        ("anode_bpp", anode_bpp),
        ("cathode_bpp", cathode_bpp),
    ]:
        if comp is None:
            continue
        label = f"{label_prefix}:{comp.id}"
        contrib = _asr_from_component(label, comp)
        if contrib is None:
            skipped.append(f"{label} — no ASR and no through-plane resistivity in spec")
        else:
            ohmic.append(contrib)

    return StackBuild(
        kinetics=kinetics,
        operating_point=op,
        ohmic=ohmic,
        skipped_layers=skipped,
    )
