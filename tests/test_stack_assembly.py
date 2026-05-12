"""assembly.stack — bridge from Library to physics inputs.

End-to-end test: load the real Library, build a stack from real entries,
run the polarisation curve through it, check the ADR-004 bands hold.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from pem_ec_designer.assembly.stack import build_stack
from pem_ec_designer.materials.loader import load_library
from pem_ec_designer.physics.polarization import cell_voltage

LIBRARY_DIR = Path(__file__).parent.parent / "library"


@pytest.fixture(scope="module")
def lib():
    return load_library(LIBRARY_DIR)


def test_build_stack_minimal_membrane_only(lib) -> None:
    """Smallest viable stack: just a membrane + catalyst Materials."""
    membrane = lib.components["membrane.nafion.212"]
    membrane_mat = lib.materials["nafion-1100"]
    iro2 = lib.materials["iro2-tio2-catalyst"]
    ptc = lib.materials["pt-c-catalyst"]

    build = build_stack(
        membrane=membrane,
        membrane_material=membrane_mat,
        anode_catalyst_material=iro2,
        cathode_catalyst_material=ptc,
        T=353.15,
        p_h2=1e5,
        p_o2=1e5,
    )

    assert math.isclose(build.kinetics.j0_anode, 1e-2)
    assert math.isclose(build.kinetics.alpha_anode, 0.75)
    assert math.isclose(build.kinetics.j0_cathode, 1e3)
    assert math.isclose(build.kinetics.alpha_cathode, 0.5)
    assert len(build.ohmic) == 1
    assert build.ohmic[0].label.startswith("membrane:membrane.nafion.212")
    assert build.skipped_layers == []


def test_build_stack_with_full_layers_runs_polarisation(lib) -> None:
    """Stack with GDL + BPP — V(1 A/cm²) must land in the Bernt-2016 band."""
    build = build_stack(
        membrane=lib.components["membrane.nafion.212"],
        membrane_material=lib.materials["nafion-1100"],
        anode_catalyst_material=lib.materials["iro2-tio2-catalyst"],
        cathode_catalyst_material=lib.materials["pt-c-catalyst"],
        anode_gdl=lib.components["gdl.sgl.39bb"],
        cathode_gdl=lib.components["gdl.sgl.39bb"],
        anode_bpp=lib.components["bpp.poco.axf5q_5mm"],
        cathode_bpp=lib.components["bpp.poco.axf5q_5mm"],
        T=353.15,
    )

    # SGL 39BB has an `area_specific_resistance_through_plane` (13 mΩ·cm²),
    # so its ASR is taken directly. Toray TGP-H has resistivity but no
    # ASR field — would be computed differently.
    assert any("gdl.sgl.39bb" in c.label for c in build.ohmic)

    # POCO AXF-5Q BPP has neither ASR nor resistivity_through_plane in
    # the Component spec — it should be skipped (the bulk σ is on the
    # Material, but a BPP is thick and its ASR is dominated by interface
    # contacts, which we don't have a value for).
    assert any("anode_bpp" in s for s in build.skipped_layers)

    point = cell_voltage(
        j=1e4,  # 1 A/cm²
        kinetics=build.kinetics,
        op=build.operating_point,
        ohmic=build.ohmic,
    )
    assert 1.50 <= point.v_cell <= 1.80, (
        f"V(1 A/cm²) = {point.v_cell:.3f} V from real Library stack — "
        f"outside expected band. Loss breakdown: "
        f"E_rev={point.e_rev:.3f}, η_OER={point.eta_oer:.3f}, "
        f"η_HER={point.eta_her:.3f}, η_ohm={point.eta_ohm:.3f}"
    )


def test_missing_kinetic_field_raises(lib) -> None:
    """If a 'catalyst' material lacks j0, build_stack must fail loudly."""
    membrane = lib.components["membrane.nafion.212"]
    membrane_mat = lib.materials["nafion-1100"]
    # Use the membrane material as if it were a catalyst — it has no j0_anode.
    with pytest.raises(ValueError, match="j0_anode"):
        build_stack(
            membrane=membrane,
            membrane_material=membrane_mat,
            anode_catalyst_material=membrane_mat,    # wrong on purpose
            cathode_catalyst_material=lib.materials["pt-c-catalyst"],
        )


def test_thinner_membrane_lowers_voltage(lib) -> None:
    """Nafion 212 (50 µm) vs 117 (183 µm) at the same j: thinner → lower V."""
    common = dict(
        membrane_material=lib.materials["nafion-1100"],
        anode_catalyst_material=lib.materials["iro2-tio2-catalyst"],
        cathode_catalyst_material=lib.materials["pt-c-catalyst"],
        T=353.15,
    )
    build_thin = build_stack(membrane=lib.components["membrane.nafion.212"], **common)
    build_thick = build_stack(membrane=lib.components["membrane.nafion.117"], **common)

    v_thin = cell_voltage(j=1e4, kinetics=build_thin.kinetics,
                          op=build_thin.operating_point, ohmic=build_thin.ohmic).v_cell
    v_thick = cell_voltage(j=1e4, kinetics=build_thick.kinetics,
                           op=build_thick.operating_point, ohmic=build_thick.ohmic).v_cell
    assert v_thin < v_thick
