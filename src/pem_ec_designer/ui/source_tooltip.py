"""Source-Tooltip helper — every numeric spec gets its BibTeX key on hover.

UX-VISION P3 ("Quelle hinter jedem Wert"). Pure formatting helper —
no Qt imports needed, so it stays testable as a string function and the
widget layer just calls `setToolTip(format_source_tooltip(...))`.

Inputs are `SourcedValue` instances from `schema/source.py`. The output
is a small HTML snippet because Qt tooltips render rich text when the
string contains an HTML tag.
"""

from __future__ import annotations

from typing import Any

from ..schema.source import SourcedValue


def _format_value(v: Any) -> str:
    """Best-effort scalar/unit pretty-print without forcing imports."""
    if hasattr(v, "value") and hasattr(v, "unit"):
        return f"{v.value:g} {v.unit}"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def format_source_tooltip(sv: SourcedValue, label: str | None = None) -> str:
    """Render a `SourcedValue` as an HTML tooltip snippet.

    Layout (short, scannable):
        <b>{label}</b>            (optional)
        {value} {unit}
        Source: <code>{bibkey}</code>
        Confidence: {confidence}
        Note: {note}              (optional)

    Returns plain text if the SourcedValue is unusable (defensive — no
    raises from a formatting helper).
    """
    if sv is None:
        return ""
    lines: list[str] = []
    if label:
        lines.append(f"<b>{label}</b>")
    lines.append(_format_value(sv.value))
    lines.append(f"Source: <code>{sv.source}</code>")
    lines.append(f"Confidence: {sv.confidence}")
    if sv.note:
        lines.append(f"<i>{sv.note}</i>")
    return "<br>".join(lines)


def format_thickness_tooltip(component: Any) -> str:
    """Tooltip for a Component using its `thickness` SourcedValue."""
    if component is None or not hasattr(component, "thickness"):
        return ""
    return format_source_tooltip(component.thickness, label=f"Thickness · {component.id}")


def format_material_kinetics_tooltip(material: Any, role: str) -> str:
    """Tooltip for a catalyst Material, citing j0 + α for the given role.

    Args:
        material: schema.Material
        role: "anode" or "cathode"
    """
    if material is None:
        return ""
    j0 = getattr(material, f"j0_{role}", None)
    alpha = getattr(material, f"alpha_{role}", None)
    sigma = getattr(material, "sigma_S_per_m", None)
    parts: list[str] = [f"<b>{material.name}</b>"]
    if j0 is not None:
        parts.append(f"j₀,{role} = {_format_value(j0.value)} · <code>{j0.source}</code>")
    if alpha is not None:
        parts.append(f"α,{role} = {_format_value(alpha.value)} · <code>{alpha.source}</code>")
    if sigma is not None:
        parts.append(f"σ = {_format_value(sigma.value)} · <code>{sigma.source}</code>")
    if len(parts) == 1:
        return f"<b>{material.name}</b><br><i>no cited kinetic values</i>"
    return "<br>".join(parts)
