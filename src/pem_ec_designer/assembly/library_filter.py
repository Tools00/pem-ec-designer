"""Library filters — pure helpers for category- and capability-based selection.

ADR-006 §Filter-Spezifikation. Eight functions, each takes a `Library`
and returns a category-filtered, deterministically-sorted list of IDs.

No Qt imports here — the UI layer (`ui/stack_composer.py`) consumes
these lists but does not implement the filter logic.
"""

from __future__ import annotations

from ..materials.loader import Library


def _sort_by_thickness(lib: Library, category: str) -> list[str]:
    """IDs of all components in `category`, sorted by ascending thickness."""
    ids = [cid for cid, c in lib.components.items() if c.category == category]
    return sorted(ids, key=lambda cid: lib.components[cid].thickness.value.value_si)


def _sort_alpha(lib: Library, category: str) -> list[str]:
    """IDs of all components in `category`, alphabetically sorted."""
    return sorted(cid for cid, c in lib.components.items() if c.category == category)


# ── component filters ─────────────────────────────────────────────────


def membranes(lib: Library) -> list[str]:
    return _sort_by_thickness(lib, "membrane")


def anode_catalyst_layers(lib: Library) -> list[str]:
    return _sort_alpha(lib, "anode_cl")


def cathode_catalyst_layers(lib: Library) -> list[str]:
    return _sort_alpha(lib, "cathode_cl")


def gas_diffusion_layers(lib: Library) -> list[str]:
    return _sort_by_thickness(lib, "gdl")


def bipolar_plates(lib: Library) -> list[str]:
    return _sort_alpha(lib, "bpp")


# ── material filters ──────────────────────────────────────────────────


# Materials with σ are either ionic ionomers (~ 5–15 S/m, membranes) or
# graphitic BPP substrates (~ 10⁴–10⁵ S/m, six orders larger). One
# decade as cut-off (100 S/m) is robust and avoids needing a schema
# `category` field for v1.0. Documented in ADR-006.
_MEMBRANE_SIGMA_MAX_S_PER_M: float = 1.0e2


def membrane_materials(lib: Library) -> list[str]:
    """Materials with an ionic conductivity (σ < 100 S/m) — usable as membrane material.

    The σ-cut-off rejects graphitic BPP substrates (poco-axf5q at 6.8e4 S/m)
    while keeping all PFSA-class ionomers.
    """
    def is_membrane(m) -> bool:
        sigma = getattr(m, "sigma_S_per_m", None)
        if sigma is None:
            return False
        if getattr(m, "j0_anode", None) is not None:
            return False
        if getattr(m, "j0_cathode", None) is not None:
            return False
        return sigma.value.value_si < _MEMBRANE_SIGMA_MAX_S_PER_M

    return sorted(mid for mid, m in lib.materials.items() if is_membrane(m))


def anode_catalyst_materials(lib: Library) -> list[str]:
    """Materials with a j0_anode field — usable as anode catalyst."""
    return sorted(
        mid for mid, m in lib.materials.items()
        if getattr(m, "j0_anode", None) is not None
    )


def cathode_catalyst_materials(lib: Library) -> list[str]:
    """Materials with a j0_cathode field — usable as cathode catalyst."""
    return sorted(
        mid for mid, m in lib.materials.items()
        if getattr(m, "j0_cathode", None) is not None
    )
