"""Flow-field geometry generator.

A flow-field plate is an extruded footprint MINUS a channel pattern.
Currently supports: `straight_parallel`. Other patterns
(`serpentine`, `interdigitated`, `mesh`, `pin_fin`) will land as the
project needs them — `NotImplementedError` documents the gap.

Why a dedicated generator (not `build_extruded`): flow-fields are the
first non-pure-extrusion components. They require boolean subtraction
of a channel pattern from a base plate.

Conventions:
- Channels run along the local X axis.
- Channels are open on both ends (cut all the way through in X).
- Channel cross-section = rectangle (width by depth).
- Channels are centred on the footprint by symmetric pitch.
"""

from __future__ import annotations

from build123d import Box, Location, Part

from ..schema import FlowField
from .extruded import build_extruded

_M_TO_MM = 1000.0


def build_flow_field(spec: FlowField) -> Part:
    """Return a build123d Part for the given flow-field spec.

    For `straight_parallel`: builds the base plate via `build_extruded`,
    then subtracts N parallel channels (N = floor((W - cw) / pitch) + 1).
    """
    if spec.pattern != "straight_parallel":
        raise NotImplementedError(
            f"flow-field pattern {spec.pattern!r} not implemented yet"
        )

    for field_name in ("channel_width", "channel_depth", "channel_pitch"):
        if getattr(spec, field_name) is None:
            raise ValueError(
                f"{spec.id!r}: straight_parallel requires {field_name}"
            )
    if spec.footprint is None or spec.footprint.shape not in ("square", "rectangular"):
        raise ValueError(
            f"{spec.id!r}: straight_parallel requires a rectangular footprint"
        )

    plate = build_extruded(spec)

    cw_mm = spec.channel_width.value.value_si * _M_TO_MM     # type: ignore[union-attr]
    cd_mm = spec.channel_depth.value.value_si * _M_TO_MM     # type: ignore[union-attr]
    pitch_mm = spec.channel_pitch.value.value_si * _M_TO_MM  # type: ignore[union-attr]
    plate_w_mm = spec.footprint.width.value_si * _M_TO_MM    # type: ignore[union-attr]
    plate_h_mm = (
        spec.footprint.height.value_si * _M_TO_MM            # type: ignore[union-attr]
        if spec.footprint.height
        else plate_w_mm
    )
    plate_t_mm = spec.thickness.value.value_si * _M_TO_MM

    if pitch_mm < cw_mm:
        raise ValueError(
            f"{spec.id!r}: channel_pitch ({pitch_mm:g} mm) < "
            f"channel_width ({cw_mm:g} mm) — channels would overlap"
        )
    if cd_mm >= plate_t_mm:
        raise ValueError(
            f"{spec.id!r}: channel_depth ({cd_mm:g} mm) >= "
            f"plate thickness ({plate_t_mm:g} mm) — would cut through"
        )

    # Number of channels that fit centred along Y. Take the channel-axis
    # span as plate_h (channels along X, distributed along Y).
    n_channels = int((plate_h_mm - cw_mm) // pitch_mm) + 1
    if n_channels < 1:
        raise ValueError(f"{spec.id!r}: footprint too narrow for any channel")

    # Centre the channel bank along Y.
    span = (n_channels - 1) * pitch_mm
    y0 = -span / 2.0
    # Channels open on the top face of the plate (positive Z).
    z_centre = (plate_t_mm - cd_mm) / 2.0

    result = plate
    for i in range(n_channels):
        channel = Box(length=plate_w_mm, width=cw_mm, height=cd_mm)
        channel = Location((0.0, y0 + i * pitch_mm, z_centre)) * channel
        result = result - channel  # build123d boolean subtraction

    return result
