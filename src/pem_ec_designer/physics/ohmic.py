"""Ohmic losses — linear ASR aggregation across a stack.

ADR-004 §Decision D1: total ohmic voltage drop is
    η_ohm(j) = j · Σ ASR_i
with each ASR_i either pulled directly from a component spec (already
in [Ω·m²]) or computed from material conductivity and component thickness
    ASR = thickness / σ.

This is the simplest possible model. It assumes:
  - Current flows perpendicular to component layers (1-D path).
  - No constriction effects from flow-field land/channel geometry
    (rejected D2 in ADR-004 — would need 2-D).
  - Contact resistances between layers are either captured in the
    component-level area_specific_resistance_through_plane (e.g. SGL
    datasheet values report this "at 1 MPa compression") or ignored.

Inputs in SI: j in A/m², ASR in Ω·m². Output η_ohm in V.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OhmicContribution:
    """One layer's ohmic contribution — kept structured for waterfall display."""

    label: str
    asr: float  # Ω·m²

    def voltage_drop(self, j: float) -> float:
        return j * self.asr


def total_asr(contributions: list[OhmicContribution]) -> float:
    """Sum of layer ASRs — linear series-resistor model.

    Raises:
        ValueError: any contribution has negative ASR.
    """
    for c in contributions:
        if c.asr < 0:
            raise ValueError(f"negative ASR in '{c.label}': {c.asr}")
    return sum(c.asr for c in contributions)


def ohmic_overpotential(
    j: float,
    contributions: list[OhmicContribution],
) -> float:
    """η_ohm(j) = j · ΣASR. Linear, no current-dependence beyond that."""
    return j * total_asr(contributions)


def asr_from_thickness_and_conductivity(thickness_m: float, sigma_s_per_m: float) -> float:
    """ASR = L / σ for a bulk-conductivity layer (membrane is the canonical case).

    Args:
        thickness_m:   layer thickness in metres.
        sigma_s_per_m: through-plane conductivity in S/m.

    Returns:
        ASR in Ω·m².

    Raises:
        ValueError: non-positive inputs.
    """
    if thickness_m <= 0:
        raise ValueError(f"thickness must be > 0 m, got {thickness_m}")
    if sigma_s_per_m <= 0:
        raise ValueError(f"sigma must be > 0 S/m, got {sigma_s_per_m}")
    return thickness_m / sigma_s_per_m
